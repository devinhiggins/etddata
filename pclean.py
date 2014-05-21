# Special function to clean up the program name based on known issues.

def Program_Clean(program):
    if " - Master" in program:
        clean_program = program[:program.index("- Master")].rstrip()
    elif " - Doctor" in program:
        clean_program = program[:program.index("- Doctor")].rstrip()
    else:
        clean_program = program

    if clean_program == "Pharmacology and Toxicology - Environmental Toxicology":
        clean_program = "Pharmacology and Toxicology-Environmental Toxicology"
    elif clean_program == "Higher, Adult, and Lifelong Education":
        clean_program = "Higher, Adult and Lifelong Education"
    elif clean_program == "Comparative Med & Integr Biol":
        clean_program = "Comparative Medicine and Integrative Biology"
    elif clean_program == "Animal Science- Doctor of Philosophy":
        clean_program = "Animal Science"
    elif clean_program == "Crop and Soil Sciences- Doctor of Philosophy":
        clean_program = "Crop and Soil Sciences"
    elif clean_program == "Business Administration - Organization Behavior - Huamn Resource Management":
        clean_program = "Business Administration - Organization Behavior - Human Resource Management"
    elif clean_program == "English" or clean_program == "Literature in English":
        clean_program = "English & Literature in English"
    elif clean_program == "Biological Science-Interdepartmental":
	clean_program = "Biological Science - Interdepartmental"
	
    return clean_program
