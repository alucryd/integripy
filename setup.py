from setuptools import setup

setup(
    name='integripy',
    packages=['integripy'],
    include_package_data=True,
    install_requires=[
        'flask',
        'click',
        'humanize'
    ],
)
