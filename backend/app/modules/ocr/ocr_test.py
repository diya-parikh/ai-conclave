import asyncio
import sys
import os

sys.path.insert(0, r"C:\Users\ruler\Desktop\Capstone\evaluate-ai-capstone-main\backend\app\modules\ocr")

from app.modules.ocr.service import OCRService

async def main():
    pdf_path = r"C:\Users\ruler\Desktop\Capstone\evaluate-ai-capstone-main\backend\app\modules\ocr\inputs\DL.pdf"

    if not os.path.exists(pdf_path):
        print(f"ERROR: File not found: {pdf_path}")
        return

    print(f"Processing: {pdf_path}")
    service = OCRService()
    docx_path = await service.process(pdf_path, "application/pdf")
    print(f"\nDone! Open your results at:\n{docx_path}")

asyncio.run(main())