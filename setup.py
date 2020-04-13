from setuptools import find_packages, setup

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='jellyfin-accounts',
    version='0.1',
    scripts=['jf-accounts'],
    author="Harvey Tindall",
    author_email="hrfee@protonmail.ch",
    description="A simple invite system for Jellyfin",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hrfee/jellyfin-accounts",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    # include_package_data=True,
    data_files=[('data', ['data/config-default.ini',
                          'data/email.html',
                          'data/email.mjml',
                          'data/email.txt']),
                ('data/static', ['data/static/admin.js']),
                ('data/templates', [
                          'data/templates/404.html',
                          'data/templates/invalidCode.html',
                          'data/templates/admin.html',
                          'data/templates/form.html'])],
    zip_safe=False,
    install_requires=[
        'Flask',
        'flask_httpauth',
        'requests',
        'itsdangerous',
        'passlib',
        'secrets',
        'pytz',
        'python-dateutil',
        'watchdog',
        'configparser',
        'pyOpenSSL',
        'waitress',
    ],
)

