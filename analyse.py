from langchain_groq import ChatGroq
from langchain_community.document_loaders import Docx2txtLoader
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os
import base64
import json
import re
from groq import Groq

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class AnalysisNode:
    """
    Extracts UI components, API contracts, and folder structure from the SRD document,
    and generates detailed file descriptions.

    For every Angular component (or page), it outputs three objects:
      - One for the .component.ts file.
      - One for the .component.html file.
      - One for the .component.css file.
    Service files or app-level files are generated as single objects.
    """

    def __init__(self):
        """Initialize Analysis Node and process the document & images."""
        current_directory = os.getcwd()

# Set your base folder path to the current directory
        self.folder_path = current_directory
        self.docx_path = os.path.join(self.folder_path, "books", "frontend.docx")  # SRD file path
        self.image_folder = os.path.join(self.folder_path, "screenshots")  # Screenshots folder

        # Load and process the document
        self.document_text = self.load_document()
        print(f"✅ Loaded document with {len(self.document_text.split())} words.")

        # Process screenshots (if any)
        self.screenshot_data = self.process_screenshots()

        # Initialize LLM for structured extraction
        self.llm_text = ChatGroq(model_name="llama3-8b-8192", api_key=GROQ_API_KEY)

    def load_document(self):
        """Loads and extracts text from the .docx document."""
        if not os.path.exists(self.docx_path):
            raise FileNotFoundError(f"Document not found: {self.docx_path}")
        loader = Docx2txtLoader(self.docx_path)
        docs = loader.load()
        return " ".join([page.page_content for page in docs])

    def encode_image(self, image_path):
        """Encodes an image to Base64 format."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def process_screenshots(self):
        """Uses an AI Vision model to analyze UI details from screenshots."""
        if not os.path.exists(self.image_folder):
            print("⚠️ No screenshots found.")
            return {}

        client = Groq(api_key=GROQ_API_KEY)
        screenshot_data = {}

        for image_file in os.listdir(self.image_folder):
            if image_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_path = os.path.join(self.image_folder, image_file)
                base64_image = self.encode_image(image_path)
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Extract UI components, layout structure, and text from this image."},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                            ],
                        }
                    ],
                    model="llama-3.2-11b-vision-preview",
                )
                extracted_text = chat_completion.choices[0].message.content.strip()
                screenshot_data[image_file] = extracted_text

        return screenshot_data

    def extract_folder_structure(self):
        """
        Extracts the Angular folder structure from the SRD and screenshot data.
        Appends an Angular initialization command at the end.
        """
        prompt = PromptTemplate.from_template("""
You are an expert in Angular development.
Given the Software Requirements Document (SRD) of an Angular project:

{document_text}

and the extracted UI details from screenshots:

{screenshot_data}

Generate a **hierarchical structured folder representation** of the project using the following format:

- Use `DIR:` for folders
- Use `CMP:` for Angular components (which consist of multiple files)
- Use `SRV:` for Angular services
- Use `PAGE:` for page components(which consists of multiple files)
- Use `ST:` for state management files
- Use `FILE:` for standalone files
dont mix services with components or pages write all services in seperate folder itself
Maintain the hierarchy with proper indentation.

Example:
DIR: angularapp
DIR: features
DIR: dashboard
DIR: CMP: dashboard.component
DIR: CMP: dashboard.tiles.component
DIR: CMP: dashboard.search.component
DIR: SRV: dashboard.service
DIR: PAGE: dashboard.page
DIR: ST: dashboard.store
DIR:CMP:Signup.component
DIR: features
DIR: lms
DIR: CMP: lms.component
DIR: CMP: lms.leave.component
DIR: CMP: lms.manager.component
DIR: SRV: lms.service
DIR: PAGE: lms.page
DIR: ST: lms.store
DIR: FILE: lms.constants.ts                                       

Finally, **add a command to initialize the Angular project at the end.**
""")
        message = prompt.format(
            document_text=self.document_text,
            screenshot_data="\n".join(self.screenshot_data.values())
        )
        response = self.llm_text.invoke(message)
        folder_structure = response.content.strip() + "\n\nINIT: Run 'ng new AngularApp --skip-install --style=scss --routing'"
        return folder_structure

    def extract_file_descriptions(self, folder_structure):
        """
        Generates detailed file descriptions from the folder structure.
        IMPORTANT: For now, return the raw LLM output.
        The prompt should instruct the LLM to return a JSON array of objects,
        where for each Angular component or page, three objects are generated:
          - One for the TypeScript file (fileName: {{componentName}}.component.ts)
          - One for the HTML file (fileName: {{componentName}}.component.html)
          - One for the CSS file (fileName: {{componentName}}.component.css)
        For services, a single object is generated.
        """
        prompt = PromptTemplate.from_template("""
Generate detailed file descriptions from the following folder structure.
    {folder_structure}
IMPORTANT: Return a JSON array of objects.
For each Angular component or page, output three objects:
  - One for the TypeScript file (fileName: {{componentName}}.component.ts)
  - One for the HTML file (fileName: {{componentName}}.component.html)
  - One for the CSS file (fileName: {{componentName}}.component.css)
For services, output one object (e.g., fileName: auth.service.ts).
For application-level modifications (such as app.component or routing files), output as needed.
Each object should have:
  - "type": For components use "CMP" (or "PAGE" for pages), for services "SRV", for app modifications "APP" or "ROUTES".
  - "fileName": the name of the file.
  - "description": a concise one-sentence description of the file's purpose.
you should write for each and every component each and every page each and every service

The JSON array should look like this:
[
  {{
    "type": "CMP",
    "fileName": "button.component.ts",
    "description": "Implements the logic for a generic button component."
  }},
  {{
    "type": "CMP",
    "fileName": "button.component.html",
    "description": "Provides the markup for a generic button component."
  }},
  {{
    "type": "CMP",
    "fileName": "button.component.css",
    "description": "Defines the styles for a generic button component."
  }}
]
Return only the JSON array.
""")
        message = prompt.format(folder_structure=folder_structure)
        response = self.llm_text.invoke(message)
        # For now, we simply return the raw output without JSON parsing.
        return response.content.strip()

    def save_analysis_output(self, folder_structure, file_descriptions):
        """Saves the folder structure and file descriptions to disk."""
        folder_structure_path = os.path.join(self.folder_path, "folder_structure.txt")
        file_desc_path = os.path.join(self.folder_path, "file_descriptions.txt")

        with open(folder_structure_path, "w", encoding="utf-8") as txt_file:
            txt_file.write(folder_structure)

        with open(file_desc_path, "w", encoding="utf-8") as txt_file:
            txt_file.write(file_descriptions)

        print(f"✅ Saved folder structure: {folder_structure_path}")
        print(f"✅ Saved file descriptions: {file_desc_path}")

if __name__ == "__main__":
    analysis_node = AnalysisNode()

    print("\n🔹 Extracting folder structure...")
    folder_structure = analysis_node.extract_folder_structure()

    print("\n🔹 Generating file descriptions (JSON)...")
    file_descriptions = analysis_node.extract_file_descriptions(folder_structure)

    print("\n🔹 Saving extracted results...")
    analysis_node.save_analysis_output(folder_structure, file_descriptions)

    print("\n🚀 Analysis completed successfully!")
