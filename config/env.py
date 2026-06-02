class Env:
    SPREADSHEET_ID_A = "1sqrKm8z6by6G-J5E1uLISCzCBVvK_S2Nvg6-e6Aqbec"
    SPREADSHEET_ID_B = "1T8uDx8yYscudLaY777woX5uXd5cGY5N1kMRgEYGAvhY"
    N_STUDENT_A = 22
    N_STUDENT_B = 36
    COURSE_ID_A = "825125683344"
    COURSE_ID_B = "825266594962"
    API_URL = "http://localhost:3000"

    def get_config(self, course_code):
        if course_code == "b":
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
