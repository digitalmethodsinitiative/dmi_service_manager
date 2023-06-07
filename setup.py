from setuptools import setup

# Universal packages
packages = [
	"Flask",
	"flask_shell2http",
	"gunicorn",
	"pyyaml"
]


setup(
	name='dmi_service_manager',
	version="1.0",
	description="DMI Service Manager is a server that runs services on request",
	author="Open Intelligence Lab",
	author_email="4cat@oilab.eu",
	url="https://oilab.eu",
	python_requires='>=3.7',
	install_requires=packages,
)
