from .block_type import BlockType


class Block:

    def __init__(self, block_type: BlockType, content: str):
        """
        Initializes a new instance of the Block class.

        Args:
            block_type (BlockType): The type of the block, represented by a BlockType instance.
            content (str): The content of the block.
        """
        self._block_type = block_type
        self._content = content

        # Name if no name is given
        # Name is assigned inside the agent class
        self._placeholder_name = "{block_name}"

    @classmethod
    def from_string(cls, block_type: BlockType, string_block: str):
        """
        Initializes a block object from its string representation and block_type

            Args:
                string_block (str): The full string representation of the block.
                block_type (BlockType): The type of the block to initialize.

        """
        content = block_type.get_block_content_from_string(string_block)
        return cls(block_type=block_type, content=content)

    @property
    def block_type(self):
        return self._block_type

    @property
    def content(self):
        return self._content

    def __call__(self, name=None) -> str:
        """
        Return block as string for use with LLMs

        Args:
            name (str, optional): The name of the block.
                When no name is given, uses a placeholder.

        Returns:
            str: The Block formatted as a string.
        """
        return self._get(name=name)

    def __str__(self) -> str:
        """
        Returns the string representation of the Block instance.

        Returns:
            str: The Block formatted as a string.
        """
        return self._get()

    def _get(self, name=None) -> str:
        """
        Returns the Block as full string representation.

        Args:
            name (str, optional): The name of the block.
                When no name is given, uses a placeholder.

        Returns:
            str: The Block formatted as a string.
        """
        if name is None:
            name = self._placeholder_name

        block = self._block_type.fill(name, self._content)
        return block

    def is_block_type(self, block_type: BlockType):
        """Return true if this block is of the given block_type"""
        # todo: make sure input is BlockType maybe this function does it already?
        return self._block_type.name == block_type.name


# TODO: Limits on block names and block type names, such that there are no spaces and maybe always camelcase. Have a separate function which is used both by the block_type, the block and anything else that needs a name limit. --> determine based on function naming rules of python

if __name__ == "__main__":
    block_type1 = BlockType("testBlockType")
    block = Block(block_type1, "This is the content!")
    print(block)

    block = Block(block_type1, "This is the content of the second block!")
    print(block)

    block = Block(
        BlockType("AnotherBlockType"), "This is the content of a different blocktype!"
    )
    print(block)
