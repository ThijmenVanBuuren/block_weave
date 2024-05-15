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
        input_block_types: List[BlockType],
        output_block_types: List[BlockType],
        prompt_template: str,
        default_llm = None,
    ):
        """
        Creates an agent function
        Agent can only be called with the given block types

            input_block_types: List[(str, Block)]
                Input arguments of the agent function.
                List[(variable_name, BlockType)]
            output_block_types: List[(str, Block)]
                List[(variable_name, BlockType)]
                Return arguments of the agent function.
            default_llm:
                llm to run agent with if No llm is provided in __call__
                Assumed to be callable as: llm(input_text)
        """
        # TODO: order according to the order of a function

        input_block_names, input_block_types = zip(*input_block_types.items())
        output_block_names, output_block_types = zip(*output_block_types.items())

        # Input variable types
        self.input_block_types = list(input_block_types)
        # Return variable types
        self.output_block_types = list(output_block_types)

        self.input_block_names = list(input_block_names)
        self.output_block_names = list(output_block_names)

        # TODO: format output blocks
        self.prompt_template = self._format_prompt_template(prompt_template)

        # LLM to use if none is given in __call__
        self.default_llm = default_llm

    def __call__(self, blocks, llm=None):
        return self._run(blocks=blocks, llm=llm)

    def __str__(self):
        return self.prompt_template
    
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

        # Match variable names to input blocks
        blocks_dict = self._get_dict_from_names_and_blocks(names=self.input_block_names,
                                                blocks=blocks)

        # # Activate blocks
        # for n, b in blocks_dict:
        #     blocks_dict[n] = b(name=n)
        # Only get content of blocks
        for n, b in blocks_dict.items():
            blocks_dict[n] = b.content

        # Get prompt for LLM
        full_prompt = self.prompt_template.format(**blocks_dict)

        return full_prompt
    
    def _format_prompt_template(self, prompt_template: str):
        """Fill in output blocks

        Args:
            prompt_template (str): _description_

        Returns:
            _type_: _description_
        """
        input_block_types_dict = {name: "{"+name+"}" for name in self.input_block_names}

        output_blocks_dict = self._get_dict_from_names_and_blocks(names=self.output_block_names, 
                                                         blocks=self.output_block_types)
        
        # Fill in blocks
        content = "ANSWER HERE"
        for n, bt in output_blocks_dict.items():
            block = Block(block_type=bt,
                          content=content)
            output_blocks_dict[n] = block(name=n)

        # Combine all blocks
        blocks_dict = input_block_types_dict | output_blocks_dict

        # Format template
        format_prompt = prompt_template.format(**blocks_dict)
        
        return format_prompt
    
    @staticmethod
    def _block_to_list(blocks: Union[Block, List[Block]]):
        if not isinstance(blocks, list):
            blocks = [blocks]
        return blocks
    
    @staticmethod
    def _get_dict_from_names_and_blocks(names: List[str], blocks: List[Block]):
        # return dict with names as keys and blocks as values
        # -> Could be any value really
        blocks_zip = zip(names, blocks)
        blocks_dict = {name: block for name, block in blocks_zip}

        return blocks_dict

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
    pass