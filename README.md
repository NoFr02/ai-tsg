
# AI-TSG

AI-TSG is a Python project designed to facilitate data extraction and visualization at Testo Sensor GmbH. This project acts as PoC of my bachelor thesis and also includes all the work which was done to develop the concept. So develop the extraction process and all the data analysing which was done upfront the PoC.

## Prerequisites

Before you begin, ensure you have Python installed on your system. This project has been tested with Python 3.12 and above. You can download and install Python from [python.org](https://www.python.org/downloads/).

## Setting Up Your Development Environment

To run this project, it's recommended to set up a virtual environment. This isolates your project dependencies from other Python projects. Here's how you can do it:

### 1. Clone the Repository

First, clone the repository to your local machine:

```bash
git clone https://github.com/NoFr02/recommender-tsg.git
cd recommender-tsg
```

### 2. Create a Virtual Environment

Create a virtual environment in the project directory:

#### For macOS/Linux:
```bash
python3 -m venv venv
```

#### For Windows:
```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

Before installing the dependencies, activate the virtual environment:

#### For macOS/Linux:
```bash
source venv/bin/activate
```

#### For Windows:
```bash
.\venv\Scripts\activate
```

### 4. Install Dependencies

With the virtual environment activated, install the project dependencies using:

```bash
pip install -r requirements.txt
```

## Usage

Please notice that for GDPR reasons there are no ressources included in this repository. So a huge part of the Dataanalysis would not work. For the PoC there also is a access to windchill required. 

First of all we have to fill the .env file.

```shell
Adress_Windchill="windchill.cds.testo"
USERNAME_WINDCHILL="mmuster@muster.de"
PASSWORD_WINDCHILL="muster"
PRINT_PIPESTEPS='False'
```

After that you can start the main.py in the poc directory.
```bash
python src/poc/main.py <recommender_type> <normalize> <evaluate>
```

recommender_type: cosine, euclidean, mean, weighted

normalize: true, false

evaluate: true, false