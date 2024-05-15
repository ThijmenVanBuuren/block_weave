from block_weave.core.llm import CallLM # load .env
from block_weave.core.block_type import BlockType
from block_weave.core.block import Block
from block_weave.core.agent import Agent

from langchain_core.prompts import PromptTemplate
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain_core.runnables import RunnableLambda

"""
Simplified:
V1:
- Blocks only for IO required. 

V2:
- Each Block has a format. Can e.g. be pydantic, or self defined
    - Block indicator only shown for custom format.

"""

class SimpleAgent:

    def __init__(self, prompt_template, schema):

        self.schema = schema

        self.pydantic_parser = PydanticOutputParser(pydantic_object=self.schema)
        format_instructions = self.pydantic_parser.get_format_instructions()

        self.prompt = ChatPromptTemplate.from_template(
            template=prompt_template,
            partial_variables = {
                # Mandatory field
                # TODO: we get it from the BlockType
                "format_instructions": format_instructions,
            }
        )

    def __call__(self, inp_dict, llm, do_parse=True):
        """Runs the agent by filling in args in inp_dict in prompt,
            and calling the llm

        Args:
            inp (dict): dict of text arguments
                "argument_name_in_prompt": "argument"
            llm (_type_): _description_
            do_parse (bool, optional): _description_. Defaults to True.

        Returns:
            parsed pydantic output
        """
        
        prompt = self.prompt.format(**inp_dict)
        # print(prompt)

        output = llm(prompt)

        if do_parse:
            return self.parse(output=output, llm=llm)

        return output

    def parse(self, output, llm, max_retries=1):
        # Allow any LLM to be used in Langchain
        wrapped_llm = RunnableLambda(llm)

        # Fix output according to schema and with retries
        fix_parser = OutputFixingParser.from_llm(parser=self.pydantic_parser, llm=wrapped_llm, max_retries=max_retries)

        # TODO: Retry agent

        parsed_output = fix_parser.parse(output)

        return parsed_output

def agent_select_chunk_workflow(text, llm):
    # Returns true/false if the chunk contains information relevant for 
    # Constructing a workflow

    # Make schema
    class YesNoSchema(BaseModel):
        answer: bool = Field(description="Yes or No answer to the question")

    # When is information in the text relevant for a data analysis workflow?
    # It must contain:
    # - Info about a data analysis step for processing CryoEM data.
    #   This includes: 
    #   - references to specific analysis job use (e.g. motionCor, 3D classification, among others)
    #   - Software packages used: (e.g. Relion, CryoSparc among others)
    #   - Any other reference to data analysis steps for CryoEM data.


    # Prompt template and input
    prompt_template = f"""
Assume the role of a Cryo Electron Microscopy (CryoEM) expert and expert on CryoEM data analysis.
You're determining if the "input text" below is relevant for CryoEM data analysis steps

Use this to determine if a text is relevant:
It must contain:
- Info about a data analysis step for processing CryoEM data.
    This includes: 
    - references to specific analysis job use (e.g. motionCor, 3D classification, among others)
    - Software packages used: (e.g. Relion, CryoSparc among others)

# Output format instructions:
{{format_instructions}}

# Input text:
{{text}}
    """

    # Init agent
    agent = SimpleAgent(prompt_template=prompt_template, schema=YesNoSchema)

    inp = {"text": text,
           }

    # TODO: it fails quite often to parse to boolean

    return agent(inp, llm=llm).answer

BLOCK_TYPE_TOPIC = BlockType("Topic")
BLOCK_TYPE_RESEARCH_QUESTIONS = BlockType("ResearchQuestions")
BLOCK_TYPE_SEARCH_CRITERIA = BlockType("SearchCriteria")

class TopicToResearchQuestions(Agent):
    def __init__(self, n_questions=5):
        topic_block = "topic_block"
        rq_block = "rq_block"

        input_block_types = {
            topic_block: BLOCK_TYPE_TOPIC
                }
        output_block_types = {
            rq_block: BLOCK_TYPE_RESEARCH_QUESTIONS
                }

        prompt_template = f"""
Assume the role of an algorithm of an expert scientific researcher. 
You will behave like the agent_topic_to_rq algorithm, below, which converts input_blocks into output blocks:

def agent_topic_to_rq({topic_block}: BLOCK_TYPE_TOPIC) -> BLOCK_TYPE_RESEARCH_QUESTIONS:
    '''
    Creates {n_questions} research questions related to the topic
    Args:
        {topic_block}: BLOCK_TYPE_TOPIC
            The topic for which the research questions are created
    Returns:
        {rq_block}: BLOCK_TYPE_RESEARCH_QUESTIONS
        5 research questions related to the topic
    '''
    1. Analyze {topic_block}
    2. {rq_block} = Create {n_questions} research questions

    return {rq_block}

# HERE IS YOUR INPUT:
topic_text = '{{topic_block}}'
topic_block = Block(block_type=BLOCK_TYPE_TOPIC, content=topic_text)
out = agent_rq_topic(topic_block)

# Give your answer:
print(out)
==> 
{{rq_block}}
"""
        super().__init__(input_block_types=input_block_types,
                         output_block_types=output_block_types,
                         prompt_template=prompt_template,
                         )
          
class ResearchQuestionsToSearchCriteria(Agent):
	
	def __init__(self):
		##############
		# Establish search criteria
		##############

		# Who's performing the task?
		# Use a description 
		role = "Expert scientific researcher"
		# what the agent function does
		# This is what you would write as the first line in a docstring
		summary = "Establishes initial search criteria"

		# agent signature
		# variable blocks for input
		# Defined in previous cell
		input_block_types = [BLOCK_TYPE_RESEARCH_QUESTIONS]

		# return type
		output_block_types = [BLOCK_TYPE_SEARCH_CRITERIA]

		# Block variable names
		rq_block = "rq_block"
		input_block_names = [rq_block]
		criteria_block = "criteria_block"
		output_block_names = [criteria_block]

		# The code of the function
		# Line by line what happens in this algorithm
		# reference the variables
		algorithm = [f"Determine the scope of the search criteria for the {rq_block}",
					f"Create a set of search criteria that fits the domain and subject of the {criteria_block}"]

		# example of input
		input_example = """
		- How can Automatic Speech Recognition (ASR) comply with the GDPR?
		- How can Text to speech technologies comply with the GDPR?
		- What tools are being developed to help Automatic Speech Recognition systems comply with the GDPR?
		- What privacy preserving Automatic Speech Recognition technologies exist that could aid in developing responsible AI that complies with the GDPR?
		- How to encode GDPR complying behavior into an automatic speech recognition system?
		- What speech technologies can help automatic speech recognition and text to speech technologies comply with the GDPR?
		- How to encode GDPR complying regulation into a system?
		"""
		output_example = """
		- The paper is from 2010 or later.
		- The paper mentions either GDPR, privacy, encryption, regulation or a similar word in combination with Automatic speech recognition or Text to speech. 
		- The paper is deemed subjectively sufficiently contributing to (one of) the above research questions.
		"""

		# init agent 
		super().__init__(role=role,
					summary=summary,
					input_block_types=input_block_types,
					output_block_types=output_block_types,
					input_block_names=input_block_names,
					output_block_names=output_block_names,
					input_example=input_example,
					output_example=output_example,
					algorithm=algorithm,
					)

if __name__ == "__main__":
	
	llm = CallLM(provider="openai", model="gpt-3.5-turbo")

	######
	# Agent 1
	topic_agent = TopicToResearchQuestions()
	
	# Fill in a topic here
	topic = "Eastern religions and technology" 
	inp_block = Block(block_type=BLOCK_TYPE_TOPIC,
			content=topic)


	full_prompt = topic_agent.get_full_prompt(inp_block)
	# print(full_prompt)

	# # Mock output
	# research_questions = topic_agent.mock_call(inp_block)
	# print("--------------")
	# print(research_questions)

	# LLM output
	research_questions = topic_agent(inp_block, llm=llm)
	print(research_questions)

	# ######
	# # Agent 2
	# # Show prompt
	# criteria_agent = ResearchQuestionsToSearchCriteria()

	# # Gets output block of agent 1 as input
	# search_criteria_prompt = criteria_agent.get_full_prompt(research_questions)
	# # print(search_criteria_prompt)

	# # Call agent with output of the previous agent

	# # search_criteria = criteria_agent.mock_call(research_questions)
	# search_criteria = criteria_agent(research_questions, llm=llm)
	# print("-----------")
	# print(search_criteria)



