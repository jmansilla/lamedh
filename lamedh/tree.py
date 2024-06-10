
class PreserveTreeStructureMetaClass(type):
    def __call__(cls, *args, **kwargs):
        """Called when you call MyNewClass() on classes that use this metaclass"""
        obj = type.__call__(cls, *args, **kwargs)
        obj.preserve_tree_structure()
        return obj


class TreeNode(object, metaclass=PreserveTreeStructureMetaClass):
    def preserve_tree_structure(self):
        for child in self.children():
            assert isinstance(child, TreeNode), f'Child {child} of {self} is not a TreeNode. It is a {type(child)}'
            child.parent = self
        self.parent = None

    def children(self):
        return []

    def __repr__(self):
        name = self.__class__.__name__
        return self.to_string(repr, name)

    def __str__(self):
        return self.to_string(str)
