class BiDict:
    # Dictionary Like that can be accesed by values or keys
    # Both as items or attributes
    def __init__(self, mapping) -> None:
        values = list(mapping.values())
        assert len(set(values)) == len(values)  # ensures no repeated values in
        self.original = mapping
        self.reversed = {v: k for k, v in mapping.items()}

    def keys(self):
        return self.original.keys()

    def values(self):
        return self.original.values()

    def items(self):
        return self.original.items()

    def __getattribute__(self, name):
        if name in ['original', 'reversed']:
            return super().__getattribute__(name)
        try:
            return self[name]
        except KeyError:
            pass
        return super().__getattribute__(name)

    def __getitem__(self, name):
        if name in self.original:
            return self.original[name]
        if name in self.reversed:
            return name
        raise KeyError(name)

    def __iter__(self):
        for k in self.original:
            yield k
        for k in self.reversed:
            yield k


class NameSymbolMap(BiDict):
    def symbols(self):
        return self.keys()
    def names(self):
        return self.values()
    def symbol_of(self, name):
        return self.reversed[name]
