from block_weave.core.block_type import BlockType
from block_weave.core.block import Block
from block_weave.core.agent import Agent
from block_weave.core.llm import CallLM

BLOCK_TYPE_TOPIC = BlockType("Topic")
BLOCK_TYPE_RESEARCH_QUESTIONS = BlockType("ResearchQuestions")
BLOCK_TYPE_SEARCH_CRITERIA = BlockType("SearchCriteria")

class TopicToResearchQuestions(Agent):

	def __init__(self):
		# Generate research questions

		# Who's performing the task?
		# Use a description 
		role = "Expert scientific researcher"
		# what the agent function does
		# This is what you would write as the first line in a docstring
		summary = "Creates 5 research questions related to the topic"

		# agent signature
		# variable blocks for input
		# indicate the types like we would with variables
		input_block_types = [BLOCK_TYPE_TOPIC]

		# return type
		output_block_types = [BLOCK_TYPE_RESEARCH_QUESTIONS]

		# example of input
		input_example = ["A topic for research here"]
		output_example = ["""1. RQ1
		2. RQ2
		3. RQ3
		4. RQ4
		5. RQ5"""
		]

		# Block variable names
		topic_block = "topic_block"
		input_block_names = [topic_block]
		rq_block = "rq_block"
		output_block_names = [rq_block]

		# The code of the function
		# Line by line what happens in this algorithm
		# reference the block variables
		algorithm = [f"1. Analyze {topic_block}",
					f"2. Create 5 research questions",
					f"3. return the research questions as {rq_block}"]

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
	
	topic = "Eastern religions and technology" #"GDPR and speech data"
	inp_block = Block(block_type=BLOCK_TYPE_TOPIC,
			content=topic)


	full_prompt = topic_agent.get_full_prompt(inp_block)
	# print(full_prompt)

	# Mock output
	research_questions = topic_agent.mock_call(inp_block)
	# print((type(research_questions())))

	# LLM output
	research_questions = topic_agent(inp_block, llm=llm)
	print(research_questions)

	######
	# Agent 2
	# Show prompt
	criteria_agent = ResearchQuestionsToSearchCriteria()

	# Gets output block of agent 1 as input
	search_criteria_prompt = criteria_agent.get_full_prompt(research_questions)
	# print(search_criteria_prompt)

	# Call agent with output of the previous agent

	# search_criteria = criteria_agent.mock_call(research_questions)
	search_criteria = criteria_agent(research_questions, llm=llm)
	print("-----------")
	print(search_criteria)







