class CableProbe:
    """
    This Class works as a DataStructure and should help working with CableProbes
    """

    def __init__(
        self,
        sensor_type: tuple,
        max_temp: float,
        diameter_sleeve: float,
        len_sleeve: float,
        len_cable: float,
        con_type: str,
        sapmatnr="0000",
        min_temp=0.0,
    ):

        self.sensor_type = sensor_type
        self.min_temp = min_temp
        self.max_temp = max_temp
        self.diameter_sleeve = diameter_sleeve
        self.len_sleeve = len_sleeve
        self.len_cable = len_cable
        self.con_type = con_type
        self.sapmatnr = sapmatnr

    def __str__(self) -> str:
        printer = (
            f"({self.sapmatnr}){self.sensor_type}: cable:{self.len_cable},"
            f"sleeve:{self.len_sleeve}, max:{self.max_temp}, min:{self.min_temp}, {self.con_type}"
        )
        return printer

    def __repr__(self) -> str:
        representer = (
            f"({self.sapmatnr}){self.sensor_type}: cable:{self.len_cable}, "
            f"sleeve:{self.len_sleeve}, max:{self.max_temp}, min:{self.min_temp}, {self.con_type}"
        )
        return representer
