# Voice-Powered AI SQL Assistant

![Voice-Powered AI SQL Assistant](https://img.shields.io/badge/Voice--Powered%20AI%20SQL%20Assistant-v1.0-blue.svg)
[![Releases](https://img.shields.io/badge/Releases-Check%20Here-brightgreen)](https://github.com/tugkank00/Voice-Powered-AI-SQL-Assistant-Python-GPT-LangChain/releases)

## Overview

Welcome to the **Voice-Powered AI SQL Assistant** repository. This project allows users to interact with a SQL database using voice commands. By simply asking a question, the AI generates and executes the appropriate SQL query. Additionally, it can create PDF reports based on the results. This tool combines the power of voice recognition and artificial intelligence to streamline database interactions.

## Features

- **Voice Input**: Users can ask questions using natural language.
- **SQL Query Generation**: The AI interprets the question and constructs the corresponding SQL query.
- **PDF Report Generation**: The system can generate PDF reports from query results.
- **Full-Stack Implementation**: Built with FastAPI for the backend and integrates with various front-end technologies.
- **Integration with OpenAI**: Utilizes large language models for natural language processing.
- **PostgreSQL Support**: Works seamlessly with PostgreSQL databases.
- **Speech-to-Text**: Uses Whisper AI for accurate voice recognition.

## Table of Contents

1. [Installation](#installation)
2. [Usage](#usage)
3. [Technologies Used](#technologies-used)
4. [Contributing](#contributing)
5. [License](#license)
6. [Contact](#contact)

## Installation

To set up the Voice-Powered AI SQL Assistant on your local machine, follow these steps:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/tugkank00/Voice-Powered-AI-SQL-Assistant-Python-GPT-LangChain.git
   cd Voice-Powered-AI-SQL-Assistant-Python-GPT-LangChain
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**:
   Create a `.env` file in the root directory and add the necessary configuration, such as your database connection string and OpenAI API key.

5. **Run the Application**:
   Start the FastAPI server with:
   ```bash
   uvicorn main:app --reload
   ```

## Usage

After setting up the application, you can use it by following these steps:

1. **Access the Application**:
   Open your web browser and navigate to `http://localhost:8000`.

2. **Voice Input**:
   Click the microphone icon and ask your question. For example, "What are the total sales for last month?"

3. **View Results**:
   The AI will generate the SQL query, execute it, and display the results on the screen.

4. **Generate PDF Report**:
   Click the "Generate PDF" button to create a PDF report of the results.

For more detailed instructions, check the [Releases](https://github.com/tugkank00/Voice-Powered-AI-SQL-Assistant-Python-GPT-LangChain/releases) section.

## Technologies Used

This project employs a variety of technologies:

- **Python**: The primary programming language.
- **FastAPI**: For building the web application.
- **SQLAlchemy**: For database interactions.
- **PostgreSQL**: The database management system.
- **OpenAI API**: For natural language processing.
- **Whisper AI**: For voice recognition.
- **PDF Generation Libraries**: To create PDF reports.

## Contributing

We welcome contributions to improve the Voice-Powered AI SQL Assistant. To contribute:

1. **Fork the Repository**.
2. **Create a New Branch**:
   ```bash
   git checkout -b feature/YourFeature
   ```
3. **Make Your Changes**.
4. **Commit Your Changes**:
   ```bash
   git commit -m "Add Your Feature"
   ```
5. **Push to the Branch**:
   ```bash
   git push origin feature/YourFeature
   ```
6. **Create a Pull Request**.

Please ensure your code adheres to the existing style and includes tests where applicable.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For questions or feedback, please reach out:

- **Email**: your.email@example.com
- **GitHub**: [tugkank00](https://github.com/tugkank00)

## Acknowledgments

We thank the developers of the libraries and tools used in this project. Their work has made it possible to create a powerful voice-driven SQL assistant.

## Additional Resources

For further reading, consider exploring the following topics:

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://www.sqlalchemy.org/)
- [OpenAI API Documentation](https://beta.openai.com/docs/)
- [Whisper AI Documentation](https://github.com/openai/whisper)

Feel free to check the [Releases](https://github.com/tugkank00/Voice-Powered-AI-SQL-Assistant-Python-GPT-LangChain/releases) section for updates and new features.

---

This README provides a comprehensive guide to the Voice-Powered AI SQL Assistant. We hope you find it useful and that it helps you make the most of this innovative tool.