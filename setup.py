from cx_Freeze import setup, Executable

setup(
    name = "JAM Extractor",
    version = "1.0.1",
    description = "LEGO Racers JAM extractor.",
	author = "JrMasterModelBuilder",
	license = "GNU GPLv3",
    executables = [Executable("JAMExtractor.py")]
)