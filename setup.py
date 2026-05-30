"""py2app build script for Pixel Pet.

    pip3.11 install py2app
    python3.11 setup.py py2app
    open dist/PixelPet.app
"""

from setuptools import setup

APP = ["pet.py"]
DATA_FILES = [
    ("sprite_sheet", [
        "sprite_sheet/walk_sprite.png",
        "sprite_sheet/sit_sprite.png",
    ]),
]
OPTIONS = {
    "argv_emulation": False,
    "plist": {
        "LSUIElement": True,            # hide from Dock / app switcher
        "CFBundleName": "PixelPet",
        "CFBundleDisplayName": "Pixel Pet",
        "CFBundleIdentifier": "com.pixelpet.app",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
        "NSHighResolutionCapable": True,
    },
    "packages": ["PIL"],
    "includes": ["objc", "Foundation", "AppKit"],
}

setup(
    app=APP,
    name="PixelPet",
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
