import os
from setuptools import setup, find_namespace_packages

PACKAGE_NAME = "openai_mobile"
PACKAGE_DIRNAME = os.path.join(os.path.dirname(__file__), PACKAGE_NAME)


def read_requirements(dirname=PACKAGE_DIRNAME):
    """Read requirements file of a directory to a list of requirements."""
    with open(os.path.join(PACKAGE_DIRNAME, dirname, "requirements.txt")) as f:
        return f.read().splitlines()


backends = {
    "dynamodb": "backends/dynamodb",
}

providers = {
    "twilio": "providers/twilio",
}


if __name__ == "__main__":

    extras = {
        **{
            f"{backend}-backend": read_requirements(dirname)
            for backend, dirname in backends.items()
        },
        **{
            f"{provider}-provider": read_requirements(dirname)
            for provider, dirname in providers.items()
        },
    }

    # Setup application:
    setup(
        install_requires=read_requirements(),
        extras_require=extras,
        packages=find_namespace_packages(include=[f"{PACKAGE_NAME}*"]),
    )
