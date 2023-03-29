class Static:
    def __new__(cls):
        raise TypeError('Static classes cannot be instantiated')
