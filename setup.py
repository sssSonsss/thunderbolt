from setuptools import setup

APP = ['hello.py']
OPTIONS = {
    'argv_emulation': True,
    'packages': ['PyPDF2', 'google.generativeai'],
}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
