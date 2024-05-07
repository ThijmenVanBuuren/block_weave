from typing import List, Union, Tuple
import re
import os
from pathlib import Path

from .data_loader import DataLoader
from .block_type import BlockType
from .block import Block


class Agent:
    def __init__(
        self,
        role: str,
        summary: str,
        input_block_types: List[BlockType],
        output_block_types: List[BlockType],
        input_block_names: List[str],
        output_block_names: List[str],
        input_example: List[str],
        output_example: List[str],
        algorithm: List[str],
        default_llm = None,
        prompt_template_path=str(Path(__file__).resolve().parent)+os.sep+"prompt_templates/basic1.md",
    ):
        """
        Creates an agent function
        Prepares input to be called with an llm
        Args:
            role: str
                Assigned role of agent. E.g. 'An expert programmer'
            task: str
                What the agent function does, written like the first line of a docstring. E.g. 'Writes test code given a python function'
            input_block_types: List[(str, Block)]
                Input arguments of the agent function.
                List[(variable_name, BlockType)]
            output_block_types: List[(str, Block)]
                List[(variable_name, BlockType)]
                Return arguments of the agent function.
            input_block_names: List[str]
                List of the names of the input blocks. E.g. ['input_block']
            output_block_names: List[str]
                List of the names of the output blocks. E.g. ['output_block']
            input_example: List[str]
                TODO: give programmer example
                Example of the input arguments. E.g. ['GDPR and speech data']
            output_example: List[str]
                TODO: give programmer example
                Example of the return arguments. E.g. ['1. RQ1 2. RQ2 3. RQ3 4. RQ4 5. RQ5']
            algorithm:
            default_llm:
                llm to run agent with if No llm is provided in __call__
                Assumed to be callable as: llm(input_text)
        """
        # TODO: order according to the order of a function

        # Input variable types
        self.input_block_types = input_block_types
        # Return variable types
        self.output_block_types = output_block_types

        # Input variable names
        self.input_block_names = input_block_names
        # Return variable names
        self.output_block_names = output_block_names

        # Load agent data
        self.loader = DataLoader()

        # Agent function outline
        prompt_template = self._get_prompt_template(prompt_template_path)

        # Agent function before filling in the input blocks
        # TODO: check that expected variables are in the prompt_template
        self._function_prompt = self._get_function_prompt(
            role=role,
            summary=summary,
            input_example=input_example,
            output_example=output_example,
            algorithm=algorithm,
            prompt_template=prompt_template,
        )

        # LLM to use if none is given in __call__
        self.default_llm = default_llm

    def __call__(self, blocks, llm=None):
        return self._run(blocks=blocks, llm=llm)

    def __str__(self):
        return self._function_prompt
    
    def mock_call(self, blocks=None, llm=None):
        """Return fake output for testing"""
        
        out = "THIS IS A MOCK RESPONSE FOR TESTING PURPOSES ONLY"
        output_blocks = [Block(block_type=bt, content=out) for bt in self.output_block_types]

        # return a single block if only one output block is expected
        output_blocks = self._format_output_blocks(output_blocks)

        return output_blocks


    def _run(self, blocks: List[Block], llm=None):
        """
        Call an LLM with the full prompt

        args:
            blocks: Block or List[Block]
                input block variables for the agent function
            llm:
                A large language model to input the prompt in
        Returns:
            List[Block] or Block:
            The output blocks of the agent
            len(output_blocks) output blocks given len(input_blocks) number of input blocks
        """
        # Get list for singular block input
        blocks = self._block_to_list(blocks)

        assert len(blocks) == len(
            self.input_block_types
        ), f"Expected {len(self.input_block_types)} blocks, but got {len(blocks)}"
        assert self._input_blocks_correct(
            blocks
        ), f"Expected input block types {[bt.name for bt in self.input_block_types]} but got {[b._block_type.name for b in blocks]}"

        full_prompt = self.get_full_prompt(blocks)

        # Run LLM
        output = self._run_llm(full_prompt, llm=llm)

        output_blocks = self._get_blocks_from_text(block_types=self.output_block_types, text=output)

        # TODO: Get all blocks of the output, or do something without if we don't get the blocks
        # TODO: some AI agent should fix the output if it's not correct
        #       - maybe langchain can help with the output formatting
        if not self._output_blocks_correct(output_blocks):
            print(output)
            print("------------")
            raise Exception(
                f"Expected output block types {[bt.name for bt in self.output_block_types]} but LLM returned {[b._block_type.name for b in output_blocks]}"
            )

        # return a single block if only one output block is expected
        output_blocks = self._format_output_blocks(output_blocks)

        return output_blocks
    
    def _run_llm(self, prompt: str, llm=None):
        """Call the llm or output the prompt if no llm is provided

        Args:

            llm (Any Language Model, optional): 
        """
        if llm is not None:
            return llm(prompt)
        if self.default_llm is not None:
            # TODO: log that we use the default llm
            return self.default_llm(prompt)
        # TODO: WARN that no LLM was provided
        raise Exception("No Large Language model was provided to give the prompt to \n\
            Make sure to provide an llm when calling this agent or when creating it \n\
                        Use `get_full_prompt(prompt_here)` to get the full text prompt and call the llm yourself")

    def _format_output_blocks(self, blocks):
        if len(blocks) == 1:
            return blocks[0]

    def get_full_prompt(self, blocks: List[Block]):
        """
        Fill in the input blocks in the prompt and return the full prompt
        """
        # Allow single block, no list input
        blocks = self._block_to_list(blocks)

        str_blocks = self._str_join_blocks(blocks, self.input_block_names)
        full_prompt = self._function_prompt.format(input_blocks=str_blocks)

        return full_prompt

    def _get_function_prompt(
        self,
        role: str,
        summary: str,
        input_example: List[str],
        output_example: List[str],
        algorithm: List[str],
        prompt_template: str,
    ):
        """
        Fills in the variables in the prompt template and returns it
        Only the input_blocks are not filled in, as these are not known yet

        Args:
            role (str): _description_
            task (str): _description_
            input_example (str): _description_
            output_example (str): _description_
            algorithm (List[str]): _description_
            prompt_template (str): _description_

        Returns:
            str: prompt with variables filled in
        """

        # Get examples as blocks
        # Assumes examples are in the same order as the block types
        input_example_blocks = self._example_to_block(
            input_example, self.input_block_types
        )
        output_example_blocks = self._example_to_block(
            output_example, self.output_block_types
        )

        output_blocks = self._example_to_block(
            ["ANSWER HERE"], self.output_block_types
        )

        str_alg = "\n".join(algorithm)  # Todo: format in some way?

        prompt = prompt_template.format(
            role=role,
            task=summary,
            input_example=self._str_join_blocks(input_example_blocks, block_names=self.input_block_names),
            output_example=self._str_join_blocks(output_example_blocks, block_names=self.output_block_names),
            algorithm=str_alg,
            input_blocks="{input_blocks}",
            output_blocks=self._str_join_blocks(output_blocks, block_names=self.output_block_names),
        )

        return prompt

    def _get_prompt_template(self, template_path):
        """return the prompt template"""
        # todo: prompt template as text here, but load it from a md file, such that the template can be changed easily if desired
        # return the prompt template
        template = self.loader.read_utf8_file(template_path)

        return template

    @staticmethod
    def _str_join_blocks(blocks, block_names=None):
        """
            Instantiate blocks as string and join them
            Args:
                blocks: List[Block]
                block_names: List[str]
            Returns:
                str: blocks joined as string
        ."""
        if block_names is not None:
            assert len(blocks) == len(
                block_names
            ), f"Expected {len(block_names)} block names, but got {len(blocks)}"
            str_blocks = [b(n) for b, n in zip(blocks, block_names)]
        else:
            str_blocks = [b() for b in blocks]

        return "\n".join(str_blocks)
    
    @staticmethod
    def _str_join_block_types(block_types):
        """
            Instantiate blocks as string and join them
            Args:
                blocks: List[Block]
                block_names: List[str]
            Returns:
                str: blocks joined as string
        ."""
        return "\n".join([b() for b in block_types])

    @staticmethod
    def _example_to_block(example: List[str], block_types: List[BlockType]):
        """
        Convert example string to block
        Args:
            example: str
            e.g. ["GDPR and speech data", "Another input"]
            block_type: BlockType

        Returns:
            Block: block with the content of the example
        """
        
        if isinstance(example, str):
            # Assume a single example was given, convert to a list
            example = [example]

        example_blocks = []
        for e, bt in zip(example, block_types):
            example_blocks.append(Block(block_type=bt, content=e))
        return example_blocks
    
    @staticmethod
    def _block_to_list(blocks: Union[Block, List[Block]]):
        if not isinstance(blocks, list):
            blocks = [blocks]
        return blocks

    # Input type checking. Make this in a different class? Could possibly be reused by Block, BlockType and Agent.
    def _check_blocks_correct(self, blocks: List[Block], block_types: List[BlockType]) -> bool:
        """
        Check if the blocks are of the same type as the block_types
        
        Args:
            blocks (List[Block]): The input blocks to check
            block_types (List[BlockType]): The block types to check against

        Returns:
            bool
        """
        if len(blocks) != len(block_types):
            return False

        for b, b_type in zip(blocks, block_types):

            # TODO: `isinstance` can fail if you subclass Block
            # if not isinstance(b, Block):
            #     return False
            if not b.is_block_type(b_type):
                return False
        return True

    def _input_blocks_correct(self, blocks: List[Block]) -> bool:
        """
        Check if the input blocks are of the correct type
        
        Args:
            blocks (List[Block]): The input blocks to check

        Returns:
            bool
        """
        return self._check_blocks_correct(blocks, self.input_block_types)
    
    def _output_blocks_correct(self, blocks: List[Block]) -> bool:
        """
        Check if the output blocks are of the correct type
        
        Args:
            blocks (List[Block]): The output blocks to check

        Returns:
            bool
        """
        return self._check_blocks_correct(blocks, self.output_block_types)
    
    #########
    # CONVERT TEXT TO BLOCKS
    #########
    # TODO: In a separate class? Maybe a class for handling text to blocks, BlockType, Agent
    #   - class can be called here

    def _get_blocks_from_text(self, block_types: List[BlockType], text: str) -> List[Block]:
        """
        Given a list of BlockTypes and a string output, Get all blocks as Block objects from the output, in the order of the block_types
        """

        # Get all blocks as string
        string_blocks = self._get_string_blocks_from_text(block_types=block_types, text=text)
        # Get the block for each block_type
        blocks = []
        for bt, sb in zip(block_types, string_blocks):
            block = Block.from_string(block_type=bt, string_block=sb, )
            blocks.append(block)  
            
        return blocks      

    @staticmethod
    def _get_string_blocks_from_text(block_types: Union[BlockType, List[BlockType]], text: str) -> List[str]:
        """
        Returns a list of string representations of Blocks based on the list of BlockTypes, in the order they appear in the text.
        
        Args:
            block_types (Union[BlockType, List[BlockType]]): A single BlockType object or a list of BlockType objects to search for in the text.
            text (str): The text to search for blocks.

        Returns:
            List[str]: A list of strings, each representing a found block across all specified block types.
        """
        # Ensure block_types is a list
        if not isinstance(block_types, list):
            block_types = [block_types]

        if not isinstance(text, str):
            raise TypeError("text must be a string")

        # Get all blocks
        all_matches = []
        for block_type in block_types:
            pattern = block_type.get_regex_pattern()
            for match in re.finditer(pattern, text, re.DOTALL):
                all_matches.append((match.start(), match.group(0)))  # Group 0 is the full match
                
        # Sort blocks by index order they appear in in the text
        sorted_matches = sorted(all_matches, key=lambda x: x[0])
        return [match[1] for match in sorted_matches]


if __name__ == "__main__":
    # Test showing prompt

    # Who's performing the task?
    # Use a description
    role = "Expert scientific researcher"
    # what the agent function does
    # This is what you would write as the first line in a docstring
    task = "Creates 5 research questions related to the topic"

    # agent signature
    # variable blocks for input
    # indicate the types like we would with variables
    block_topic = BlockType("Topic")
    input_block_types = [block_topic]

    # return type
    block_rqs = BlockType("ResearchQuestions")
    output_block_types = [block_rqs]

    # example of input
    # TODO: one example for each input and output block
    input_example = ["GDPR and speech data"]
    output_example = [
        "1. RQ1 \
2. RQ2 \
3. RQ3 \
4. RQ4 \
5. RQ5"
    ]

    # Block variable names
    topic_block = "topic_block"
    input_block_names = [topic_block]
    rq_block = "rq_block"
    output_block_names = [rq_block]

    # The code of the function
    # Line by line what happens in this algorithm
    # reference the variables
    # TODO: better way to refer to the input and output blocks. Can e.g. be a separate class, get input and output blocks as input OR in the agent class we just check if all input and output variables are referenced.
    algorithm = [
        f"1. Analyze '{topic_block}'",
        "2. Create 5 research questions",
        f"3. return the research questions as BlockType {block_rqs} '{rq_block}'",
    ]

    # init agent
    agent = Agent(
        role=role,
        summary=task,
        input_block_types=input_block_types,
        output_block_types=output_block_types,
        input_block_names=input_block_names,
        output_block_names=output_block_names,
        input_example=input_example,
        output_example=output_example,
        algorithm=algorithm,
    )

    # Show prompt in 2 ways:

    # 1. Before filling in the input blocks
    function_prompt = str(agent)

    # print(function_prompt)

    # Get agent output
    inp = Block(block_type=block_topic, content="GDPR and speech data")

    # 2. Full prompt
    full_prompt = agent.get_full_prompt([inp])
    print(full_prompt)

    # 3 prompts:
    # 1. Template prompt
    # 2. Prompt with variables (function prompt)
    # 3. Prompt with input blocks (full prompt)
