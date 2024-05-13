# tldr
`pip install block_weave`
# About
Welcome to block_weave! An experimental project for increasing language model predictability and ease of use, with the goal of making systems with many interacting language models (agents) easier and more fun to manage. It explores the questions:
- **What if prompts had types?** 
- **What if we could write prompts just like code?**

## Overview
This project adds types to prompts from language models, using three classes: `Block`, `BlockType`, `Agent`, this way language model input and output becomes more like regular functions.

Just like this function can only receive a `string`, and return and `int`, we can wrap specific parts of language model input/output to simulate them having specific types.
```python
def example_function(hi: str) -> int:
	return 1
```
An agent function essentially does this:
```python
def agent_function(block: BlockType("Input")) -> BlockType("Output"):
	block_output = agent(block)
	return block_output
```


![](https://github.com/ThijmenVanBuuren/block_weave/raw/main/images/overview.jpg)

`Agent` is essentially a prompt template that can receive a list of `Block`s, of the given `BlockType`s (here `BlockType("Input")`). It calls a language model and returns `Block`s of the output block types (here `BlockType("Output")`).

`Block` is a container for input or output text, with a specific `BlockType`.

`BlockType` is analogous to `type` in Python like `int` or `str`, but a `BlockType` always indicates the type of a piece of text. E.g. in `Block(block_type="Topic", content="Python programming")`, the content "Python programming" has the type "Topic", because it's in a `Block` of block_type "Topic".


![](https://github.com/ThijmenVanBuuren/block_weave/raw/main/images/agent_fit.jpg)

Only an agent with the same output type as the input type of the other agent can pass its output to another agent. Since `Agent C` has a different output type, than the input type of `Agent D`, the output of `Agent C` cannot be given to `Agent D`.

# Quick start
pypi:
```bash
pip install block_weave
```
git:
```
git clone git@github.com:ThijmenVanBuuren/block_weave.git
```
## Create a simple agent
In block_weave we explicitly define the input types and output types, as `input_blocks` and `output_blocks`
In this example we will make an agent that generates research questions, given a topic.

Function view:
```python
def agent_topic_to_rq(topic_block: BLOCK_TYPE_TOPIC) -> BLOCK_TYPE_RESEARCH_QUESTIONS:
	'''
	Creates 5 research questions related to the topic
	Args:
		topic_block: BLOCK_TYPE_TOPIC
			The topic for which the research questions are created
		
	Returns:
		rq_block: BLOCK_TYPE_RESEARCH_QUESTIONS
			5 research questions related to the topic
	'''
	1. Analyze topic_block
	2. rq_block = Create 5 research questions

	return rq_block
```

Schematic view:

![](https://github.com/ThijmenVanBuuren/block_weave/raw/main/images/demo_agent.jpg)



Imports
```python
from block_weave.core.block import Block
from block_weave.core.block_type import BlockType
from block_weave.core.agent import Agent
```

Define a new agent
```python
# Generate research questions

# Who's performing the task?
role = "an expert scientific researcher"

# what the agent function does
# This is what you would write as the first line in a docstring
summary = "Creates 5 research questions related to the topic"

# agent signature
# variable blocks for input
# indicate the types like we would with variables
BLOCK_TYPE_TOPIC = BlockType("Topic")
input_block_types = [BLOCK_TYPE_TOPIC]

# return type
BLOCK_TYPE_RESEARCH_QUESTIONS = BlockType("ResearchQuestions")
output_block_types = [BLOCK_TYPE_RESEARCH_QUESTIONS]

# example of input
# Index the same as input and output block types
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
topic_agent = Agent(role=role,
				summary=summary,
				input_block_types=input_block_types,
				output_block_types=output_block_types,
				input_block_names=input_block_names,
				output_block_names=output_block_names,
				input_example=input_example,
				output_example=output_example,
				algorithm=algorithm,
				default_llm=None,
			)
```

Input a block
```python
# The topic we want research questions for
topic = "Eastern religions and technology"
# Same BlockType as defined above
inp_block = Block(block_type=BLOCK_TYPE_TOPIC, content=topic)
```

Show the prompt
```python
full_prompt = topic_agent.get_full_prompt(inp_block)

print(full_prompt)
==>
Assume the role of an Expert scientific researcher. You will behave like an algorithm that: Creates 5 research questions related to the topic. You perform this task by converting the "input_blocks" into the "output_blocks", according to the rules of the "algorithm", like the "example" below.

# Input_blocks
## @Block Topic topic_block
|---
Eastern religions and technology
---|

# Output_blocks
## @Block ResearchQuestions rq_block
|---
ANSWER HERE
---|

# Example

## Input example
## @Block Topic topic_block
|---
A topic for research here
---|

## Output example
## @Block ResearchQuestions rq_block
|---
1. RQ1
2. RQ2
3. RQ3
4. RQ4
5. RQ5
---|

# Algorithm
1. Analyze topic_block
2. Create 5 research questions
3. return the research questions as rq_block

Give the output in the exact format of the "example".
```

Simulate using a language model, for testing:
```python
research_questions = topic_agent.mock_call(inp_block)
```
```python
print(type(research_questions))
==> 
<class 'block_weave.core.block.Block'>
```
```python
print(research_questions)
==>
## @Block ResearchQuestions {block_name}
|---
THIS IS A MOCK RESPONSE FOR TESTING PURPOSES ONLY
---|
```
Get the string content
```python
str_research_questions = research_questions()
print(type(str_research_questions))
==>
<class 'str'>
```
Call a language model

Any language model or function that receives a string and returns a string will work: llm --> call: llm()
This project supports [ollama](https://github.com/ollama/ollama) and [OpenAI api](https://openai.com/index/openai-api).
```python
# install ollama first: https://github.com/ollama/ollama
llm = CallLM(provider="ollama", model="llama3")
# Add your api key in environment/.env as OPEN_AI_API_KEY = key_here
# Available models:  https://platform.openai.com/docs/models/overview
llm2 = CallLM(provider="openai", model="gpt3.5-turbo")

# call
research_questions = topic_agent(inp_block, llm=llm)

# Or add in class definition
agent = Agent(...,
			 default_llm=llm)
```

Tested and built with Python3.10

# Folder structure
```
src/
	demo.py
	block_weave/
		core/
			agent.py
			block_type.py
			block.py
			data_loader.py
			llm.py
			prompt_templates/
				# fill in templates
	tests/
	
```

# Advanced
`TODO`
- Run files in `src/` in test environment: `python3 -m src.block_weave.core.agent`
- Extending block types by defining them as classes
- two ways to create block types
	- as class
	- as global variable `BLOCK_TYPE_DEMO = BlockType("Demo")` 
- Three ways to create agents
	- Procedural (above)
	- As classes: see `src/demo.py`
	- As functions: `TODO`
- Suggested folder structure for larger projects
	- config for models
- New prompt file templates
- Detailed description of how the code works

# Contact
https://github.com/ThijmenVanBuuren/block_weave/issues

thijmendeveloper@gmail.com