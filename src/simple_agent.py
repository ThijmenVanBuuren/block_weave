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
BLOCK_TYPE_TOPIC = BlockType("Topic")

class ResearchQuestionsSchema(BaseModel):
    research_questions: list[str] = Field(description="A list of research questions")
BLOCK_TYPE_RESEARCH_QUESTIONS = BlockType("ResearchQuestions", parser=PydanticOutputParser(pydantic_object=ResearchQuestionsSchema))

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
    # TODO: input and output example. See demo.py
    def __init__(self, n_criteria=3):
        rq_block = "rq_block"
        criteria_block = "criteria_block"
        input_block_types = {
            rq_block: BLOCK_TYPE_RESEARCH_QUESTIONS
        }
        output_block_types = {
            criteria_block: BLOCK_TYPE_SEARCH_CRITERIA
        }
        prompt_template = f"""
Assume the role of an algorithm of an expert scientific researcher. 
You will behave like the agent_rq_to_criteria algorithm, below, which converts input_blocks into output blocks:

def agent_rq_to_criteria({rq_block}: BLOCK_TYPE_RESEARCH_QUESTIONS) -> BLOCK_TYPE_SEARCH_CRITERIA:
    '''
    Establishes initial search criteria based on research questions
    Args:
        {rq_block}: BLOCK_TYPE_RESEARCH_QUESTIONS
            The research questions to establish search criteria from
    Returns:
        {criteria_block}: BLOCK_TYPE_SEARCH_CRITERIA
            The initial search criteria
    '''
    1. Determine the scope of the search criteria for the {rq_block}
    2. Create a set of {n_criteria} search criteria that fits the domain and subject of the {criteria_block}

    return {criteria_block}
    
# Example:


# HERE IS YOUR INPUT:
rq_text = '{{rq_block}}'
rq_block = Block(block_type=BLOCK_TYPE_RESEARCH_QUESTIONS, content=rq_text)
out = agent_rq_to_criteria(rq_block)

# Give your answer:
print(out)
==> 
{{criteria_block}}
"""
        super().__init__(input_block_types=input_block_types,
                         output_block_types=output_block_types,
                         prompt_template=prompt_template,
                         )
        

def auto_prompt(input_block_types: dict, output_block_types: dict, instructions=""):
    input_block_names, input_block_types = zip(*input_block_types.items())
    output_block_names, output_block_types = zip(*output_block_types.items())

    template = f"""
You're a resolver that converts the input blocks {input_block_names} to output blocks {output_block_names}.

CONVERT THESE INPUT BLOCKS:
{input_block_types}

TO THESE OUTPUT BLOCKS:
{output_block_types}
"""

    return template


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
	print(full_prompt)

	# # Mock output
	# research_questions = topic_agent.mock_call(inp_block)
	# print("--------------")
	# print(research_questions)

	# LLM output
	research_questions = topic_agent(inp_block, llm=llm)
	print(research_questions)

	######
	# Agent 2
	# Show prompt
	criteria_agent = ResearchQuestionsToSearchCriteria()

	# Gets output block of agent 1 as input
	# search_criteria_prompt = criteria_agent.get_full_prompt(research_questions)
	# print(search_criteria_prompt)

	# Call agent with output of the previous agent

	# search_criteria = criteria_agent.mock_call(research_questions)
	# search_criteria = criteria_agent(research_questions, llm=llm)
	# print("-----------")
	# print(search_criteria)



