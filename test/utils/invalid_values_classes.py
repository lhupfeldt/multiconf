from multiconf import ConfigItem, MC_REQUIRED


class McRequiredInInitL1(ConfigItem):
    def __init__(self, aa=MC_REQUIRED):
        super().__init__()
        # Moving the line below here will make tests fail!
        self.setattr('aa', default=aa, prod='hi')  # This is line 8!


class McRequiredInInitL2(McRequiredInInitL1):
    def __init__(self, aa=MC_REQUIRED):
        super().__init__(aa=aa)


class McRequiredInInitL3(McRequiredInInitL2):
    def __init__(self, aa=MC_REQUIRED):
        super().__init__(aa=aa)
