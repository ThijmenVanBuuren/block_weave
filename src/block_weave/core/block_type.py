import re


class BlockType:
    # Track unique BlockType names
    _names = set()

    def __init__(self, name: str, delimiter=("|---", "---|")): # delimiter=("<block>", "</block>")):#
        """
        Initializes a new instance of the BlockType class.

        Args:
            name (str): The name of the block type.
            delimiter (tuple, optional): The delimiters used for the block. Defaults to ("{", "}").
        """
        assert (
            name not in self._names
        ), f"Cannot create this BlockType. BlockType with name {name} already exists in this Runtime, use another name. Existing names: {self._names}"

        self._names.add(name)
        self.name = name
        self.block_start = "## @Block"
        self.delimiter = delimiter

        # Block placeholders
        # self.placeholder_block_name = "{block_name}"
        # self.placeholder_content = "{content}"

    def __call__(self) -> str:
        return self._get()

    def __str__(self):
        """
        Returns the string representation of the BlockType instance.

        Returns:
            str: The name of the block type.
        """
        return self.name

    def fill(self, block_name: str, content: str):
        """
        Fill the empty block and return it

        Args:
            block_name: str
            content: str
        """
        # todo: something cleaner?
        assert not self._contains_delimiter(
            content
        ), f"Delimiter {self.delimiter[0]} and {self.delimiter[1]} are not allowed to be in the content of a block"

        empty_block = self._get()
        return empty_block.format(block_name=block_name, content=content)

    def _get(self):
        """
        Returns the BlockType as a string representation

        Returns:
            str: The Block formatted as a string.
        """
        start = self.delimiter[0]
        end = self.delimiter[1]
        empty_block = f"{self.block_start} {self.name} {{block_name}}\n{start}\n{{content}}\n{end}"
        return empty_block

    def _contains_delimiter(self, content):
        """
        Return true if content contains one of the delimiters
        """
        return self.delimiter[0] in content or self.delimiter[1] in content
    
    #################
    # Capture blocks from string
    #################

    def get_regex_pattern(self) -> str:
        """Generates a regex pattern to identify blocks of this block type in text
        
        Returns:
            regex match: 
                group(0): full match
                group(1): block type
                group(2): block name
                group(3): block content (excluding delimiters)
        """
        # TODO: return matches separately, such that other functions can use them 
        #   and don't have to rely on the order of this pattern
        #   Maybe not use regex at all
        #   Or dissallow characters meaningful for regex
        start, end = map(re.escape, self.delimiter)
        # captures content from block_start to `end` delimiter within a block 
        pattern = rf"{re.escape(self.block_start)}\s*({re.escape(self.name)})(.*?)\s*{start}(.*?){end}"
        return pattern
    
    def get_block_info_from_string(self, string_block: str, match_type="full") -> str:
        """
        Gets the content of a string representation of a Block of this BlockType

        Args:
            string_block (str): The full string representation of the block.
            block_type (BlockType): The type of the block to initialize.
            match_type (str): Type of info to capture from the block


        Returns:
             (str): Some value from the block string, defined by match_index given the regex pattern
        """
        # Use the regex pattern, assume there is exactly one block

        capture_map = {
            "full": 0,
            "type": 1,
            "name": 2,
            "content": 3
        }

        pattern = self.get_regex_pattern()
        match = re.search(pattern, string_block, re.DOTALL)
        capture = match.group(capture_map[match_type])

        return capture
    
    def get_block_name_from_string(self, string_block: str) -> str:
        """
        Returns: name (str): Name of the block
        """
        name = self.get_block_info_from_string(string_block=string_block, match_type="name")

        return name
    
    def get_block_content_from_string(self, string_block: str) -> str:
        """
        Returns: content (str): The content of a Block object with this string type.
        """
        content = self.get_block_info_from_string(string_block=string_block, match_type="content")

        return content

    def get_block_type_from_string(self, string_block: str) -> str:
        """
        Returns: content (str): The content of a Block object with this string type.
        # TODO: we already know the block type if we use this here, 
        #       so it's unnecessary or use it somewhere else
        """
        btype = self.get_block_info_from_string(string_block=string_block, match_type="type")

        return btype


# TODO: separate input/output checking and logic operations
# TODO: Should we also get the name of the block? In case we want the name to be persistent? --> later worry about this

if __name__ == "__main__":
    block_type_test = BlockType("BlockType")
    # print(block_type_test)
    # Test get block content from string
    # string_block = "## @Block test block_name\n|---\ncontent\n---|"
    # content = block_type_test.get_block_content_from_string(string_block)
    # assert content == "content", f"Expected 'content', got {content}"

    # TODO: Test regex
    string_block = """

Blabla \n blbl

## @Block BlockType block_name
|---    


content 

here
---| 
    """
    pattern = block_type_test.get_regex_pattern()

    all_matches = []
    matches = re.finditer(pattern, string_block, re.DOTALL)
    for m in matches:
        print("m:", m)
        for i in range(0, 4):
            print("\t", i, m.group(i).strip())


    # TODO: Test constructing block


