import os
from dotenv import load_dotenv

load_dotenv()


class Env:
    SPREADSHEET_ID_A = os.getenv("SPREADSHEET_ID_A")
    SPREADSHEET_ID_B = os.getenv("SPREADSHEET_ID_B")
    N_STUDENT_A = 22
    N_STUDENT_B = 36
    COURSE_ID_A = "825125683344"
    COURSE_ID_B = "825266594962"

    def get_config(self, course_code):
        if(course_code == 'b'):
            return {
                "id": self.COURSE_ID_B,
                "spreadsheet": self.SPREADSHEET_ID_B,
                "n_student": self.N_STUDENT_B,
            }
        else:
            return {
                "id": self.COURSE_ID_A,
                "spreadsheet": self.SPREADSHEET_ID_A,
                "n_student": self.N_STUDENT_A,
            }

env = Env()
