import surfactant.plugin
from surfactant.sbomtypes import SBOM, Software
from typing import Any, Dict
import javatools.jarinfo

# TODO: Add documentation about how to install javatools
# swig and libssl-dev needs to be install on Ubuntu
# https://gitlab.com/m2crypto/m2crypto/-/blob/master/INSTALL.rst

# TODO: Pull some files off of Maven (or something) to test on

def supports_file(filetype: str) -> bool:
    return filetype in ("JAVACLASS", "JAR", "WAR", "EAR")


@surfactant.plugin.hookimpl
def extract_file_info(sbom: SBOM, software: Software, filename: str, filetype: str) -> object:
    if not supports_file(filetype):
        return None
    return extract_java_info(filename, filetype)

# Map from internal major number to Java SE version
# https://docs.oracle.com/javase/specs/jvms/se20/html/jvms-4.html#jvms-4.1-200-B.2
_JAVA_VERSION_MAPPING = {
    45: "1.1",
    46: "1.2",
    47: "1.3",
    48: "1.4",
    49: "5.0",
    50: "6",
    51: "7",
    52: "8",
    53: "9",
    54: "10",
    55: "11",
    56: "12",
    57: "13",
    58: "14",
    59: "15",
    60: "16",
    61: "17",
    62: "18",
    63: "19",
    64: "20",
}

def handle_java_class(info: Dict[str, Any], class_info: javatools.JavaClassInfo):
    # This shouldn't happen but just in-case it does don't overwrite information
    if class_info.get_this() in info["classes"]:
        return
    info["classes"][class_info.get_this()] = {}
    add_to = info["classes"][class_info.get_this()]
    (major_version, _) = class_info.get_version()
    if major_version in _JAVA_VERSION_MAPPING:
        add_to["JavaMinSEVersion"] = _JAVA_VERSION_MAPPING[major_version]
    add_to["JavaExports"] = [*class_info.get_provides()]
    add_to["JavaImports"] = [*class_info.get_requires()]


def extract_java_info(filename: str, filetype: str) -> object:
    info = {"classes": {}}
    if filetype in ("JAR", "EAR", "WAR"):
        with javatools.jarinfo.JarInfo(filename) as jarinfo:
            for class_ in jarinfo.get_classes():
                handle_java_class(info, jarinfo.get_classinfo(class_))
    elif filetype == "JAVACLASS":
        with open(filename, "rb") as f:
            class_info = javatools.JavaClassInfo()
            class_info.unpack(javatools.unpack(f))
        handle_java_class(info, class_info)
    return info
