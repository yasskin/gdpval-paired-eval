import argparse
import json
from pathlib import Path


def render(source, destination):
    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()
    application = None
    document = None
    try:
        extension = source.suffix.lower()
        if extension == ".docx":
            application = win32com.client.DispatchEx("Word.Application")
            application.Visible = False
            application.DisplayAlerts = 0
            application.AutomationSecurity = 3
            document = application.Documents.Open(str(source), ReadOnly=True, AddToRecentFiles=False, ConfirmConversions=False)
            document.ExportAsFixedFormat(str(destination), 17)
        elif extension == ".pptx":
            application = win32com.client.DispatchEx("PowerPoint.Application")
            application.AutomationSecurity = 3
            document = application.Presentations.Open(str(source), ReadOnly=True, WithWindow=False)
            document.SaveAs(str(destination), 32)
        elif extension == ".xlsx":
            application = win32com.client.DispatchEx("Excel.Application")
            application.Visible = False
            application.DisplayAlerts = False
            application.AutomationSecurity = 3
            application.AskToUpdateLinks = False
            document = application.Workbooks.Open(str(source), UpdateLinks=0, ReadOnly=True)
            application.CalculateFull()
            document.SaveCopyAs(str(destination))
        else:
            raise ValueError("Unsupported Office extension")
        return {"source": str(source), "derived": str(destination), "status": "rendered"}
    finally:
        if document is not None:
            if source.suffix.lower() == ".xlsx":
                document.Close(SaveChanges=False)
            elif source.suffix.lower() == ".docx":
                document.Close(SaveChanges=0)
            else:
                document.Close()
        if application is not None:
            application.Quit()
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    print(json.dumps(render(args.source.resolve(), args.destination.resolve())))
