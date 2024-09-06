import os, re, shutil, concurrent.futures, pytesseract as pyt, tkinter as tk
from tkinter import filedialog, messagebox as mb, Button, Label, Entry
from PIL import Image, ImageChops, ImageOps
from fitz import Document
from tqdm import tqdm

pyt.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"

dpi, option, cnt = 150, 1, 1
checkStr, outfile = "Ans:", ""
showErrors = True

def trim(im):
    bg = ImageOps.expand(im, border=1, fill="white")
    diff = ImageChops.difference(im, bg)
    bbox = diff.getbbox()
    if bbox:
        return ImageOps.expand(im.crop(bbox), border=15, fill="white")
    return im

def resize(img, amt: int):
    if amt in (0, 1):
        return img
    return ImageOps.expand(img, border=(0, 0, amt, 0), fill="white")

def process_image(i_pth: str, option: int, checkStr: str) -> None:
    global cnt
    img = Image.open(i_pth)
    data = pyt.image_to_data(img, output_type=pyt.Output.DICT, lang="eng", config="--psm 6")
    splitPoints = []
    check = checkStr.lower()
    if option not in (1, 2):
        raise ValueError(f"Option can only be 1 or 2, but it is {option}.")
    
    if option == 1:
        splitPoints = [data["top"][i] + data["height"][i] + 15 for i, text in enumerate(data["text"]) if check in text.lower()]
    else:
        splitPoints = [max(1, data["top"][i] - 10) for i, text in enumerate(data["text"]) if check in text.lower()]

    if not splitPoints:
        return

    prev = 0

    for point in splitPoints:
        cropped_img = trim(img.crop((0, prev, img.size[0], point)))
        cropped_img.save(f"{i_pth[:-9]}{cnt:04}.png", "PNG")
        cnt += 1
        prev = point

    os.remove(i_pth)

def split_image(dpath: str, pg: int) -> None:
    if not os.path.isdir(dpath):
        raise ValueError("The chosen path is not a valid directory.")
    ipaths = [f"{dpath}/p{(i+1):04}.png" for i in range(pg)]
    if not ipaths:
        raise RuntimeError("The chosen directory is empty.")
    maxw = 0
    for ipath in tqdm(ipaths, desc="Processing", unit="img"):
        process_image(ipath, option, checkStr)
    maxw = max(Image.open(os.path.join(dpath+'/', ipath)).size[0] for ipath in os.listdir(dpath))
    for ipath in tqdm(os.listdir(dpath), desc="Resizing", unit="img"):
        img = Image.open(os.path.join(dpath+'/', ipath))
        resized_img = resize(img, maxw-img.size[0])
        resized_img.save(os.path.join(dpath+'/', ipath), "PNG")

def select_file() -> None:
    file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")], title="Select a PDF file")
    result = ""
    if file_path:
        dirPath = filedialog.askdirectory(title="Select Destination Folder")
        if os.path.isdir(dirPath):
            if os.listdir(dirPath):
                if not mb.askyesno("WARNING", "WARNING: The directory selected is NOT empty, which will delete all the files in the directory. Do you want to continue?"):
                    mb.showinfo("Aborted", "The operation was canceled by the user.")
                    return
                shutil.rmtree(dirPath)
                os.mkdir(dirPath)
            try:
                file = Document(file_path)
                PAGES = len(file)
                print()
                for i, page in tqdm(enumerate(file), total=PAGES, desc="Converting", unit="pg"):
                    pix = page.get_pixmap(dpi=dpi)
                    pix.save(f"{dirPath}/p{(i+1):04}.png", "PNG")
                input()
                split_image(dirPath, PAGES)
                result = f"Successfully split {PAGES} images into their respective questions."
                mb.showinfo("Result", result)
            except Exception as error:
                result = "Error occurred while processing the PDF file."
                mb.showerror("Error", f"{result}\n\n{str(error)}")
        else:
            result = "No destination folder selected."
            mb.showinfo("Result", result)
    else:
        result = "No PDF file selected."
        mb.showinfo("Result", result)

def show_message_box() -> None:
    settingWindow = tk.Toplevel()
    settingWindow.title("Settings")
    
    def readShowErr(ch : str) -> bool:
        if (ch.lower() not in ['y', 'n']):
            raise ValueError("Input field for show errors must be y or n, case-insensitive.")
        return True if (ch.lower() == 'y') else False
    
    def readOption(ch : str) -> int:
        if (ch not in ['1', '2']):
            raise ValueError("Input field for option must be 1 or 2.")
        return int(ch)
    
    def readOutput() -> None:
        global outfile
        outfile = filedialog.askopenfilename(title="Select an output file")

    split_notice = Label(settingWindow, text="SPLITTER", bg="black", fg="white", font=("Arial", 17), relief=tk.FLAT, width=15, height=1)
    split_notice.pack(padx=15, pady=(10, 7))

    dpi_label = Label(settingWindow, text="DPI (default 150)", bg="lightblue", fg="darkblue", font=("Arial", 10), relief=tk.FLAT, width=22, height=1)
    dpi_label.pack(pady=3)

    dpi_entry = Entry(settingWindow, bg="lightgreen", fg="darkblue", font=("Arial", 10), relief=tk.GROOVE, bd=2, highlightcolor="green", cursor="ibeam", width=25)
    dpi_entry.pack(pady=(0,10))

    option_label = Label(settingWindow, text="Option (default 1), 1 or 2", bg="lightblue", fg="darkblue", font=("Arial", 10), relief=tk.FLAT, width=22, height=1)
    option_label.pack(pady=3)

    option_entry = Entry(settingWindow, bg="lightgreen", fg="darkblue", font=("Arial", 10), relief=tk.GROOVE, bd=2, highlightcolor="green", cursor="ibeam", width=25)
    option_entry.pack(pady=(0,10))

    string_label = Label(settingWindow, text="Check (default \"Ans:\")", bg="lightblue", fg="darkblue", font=("Arial", 10), relief=tk.FLAT, width=22, height=1)
    string_label.pack(pady=3)

    string_entry = Entry(settingWindow, bg="lightgreen", fg="darkblue", font=("Arial", 10), relief=tk.GROOVE, bd=2, highlightcolor="green", cursor="ibeam", width=25)
    string_entry.pack(pady=(0,10))

    extract_notice = Label(settingWindow, text="EXTRACTOR", bg="black", fg="white", font=("Arial", 17), relief=tk.FLAT, width=15, height=1)
    extract_notice.pack(padx=15, pady=10)
    
    show_err_label = Label(settingWindow, text="Show Errors (default yes) y/n", bg="lightblue", fg="darkblue", font=("Arial", 10), relief=tk.FLAT, width=22, height=1)
    show_err_label.pack(pady=3)

    show_err_entry = Entry(settingWindow, bg="lightgreen", fg="darkblue", font=("Arial", 10), relief=tk.GROOVE, bd=2, highlightcolor="green", cursor="ibeam", width=25)
    show_err_entry.pack(pady=(0,10))

    output_button = Button(settingWindow, text="Select Output File", command=readOutput, bg="pink", fg="black", font=("Arial", 10), relief=tk.RAISED, width=22, height=1, cursor="hand2")
    output_button.pack(pady=(3, 10))
        
    def process_inputs() -> None:
        global dpi, checkStr, option, showErrors, outfile
        errorList = []
        try:
            dpi = int(dpi_entry.get()) if (len(dpi_entry.get()) > 0) else 150
        except:
            errorList.append("DPI entry MUST be a positive integer.\n")
        try:
            option = readOption(option_entry.get()) if (len(option_entry.get()) > 0) else 1
        except:
            errorList.append("Option entry MUST be either 1 or 2.\n")
        try:
            checkStr = string_entry.get() if (len(string_entry.get()) > 0) else "Ans:"
        except:
            errorList.append("An unknown error occurred while reading the check string.\n")
        try:
            showErrors = readShowErr(show_err_entry.get()) if (len(show_err_entry.get()) > 0) else True
        except:
            errorList.append("Input field for SHOW ERRORS must be y or n, case-insensitive.\n")
        if (len(errorList) > 0):
            errorMessage = "THE FOLLOWING ERRORS OCCURRED:\n"
            for error in errorList:
                errorMessage += error
            errorMessage += "\nPlease re-enter your values in settings."
            mb.showinfo("ERRORS", errorMessage)
            return
        message = f"DPI: {dpi}\nOption: {option}\nCheck String: \"{checkStr}\"\nShow Errors: {showErrors}\nOutput File: {outfile if (len(outfile) > 0) else None}\n\nIf you want to change these, go back to settings."
        settingWindow.destroy()
        mb.showinfo("Input Values", message)

    finish_button = Button(settingWindow, text="Save", command=process_inputs, width=10, height=1, font=("Arial", 12), bg="yellow", fg="black", cursor = "hand2")
    finish_button.pack(padx=50, pady=(10, 20))

def separater() -> None:
    dirPath = filedialog.askdirectory(title="Select Folder to Split") + '/'
    result = ""
    skippedFiles = 0

    try:
        if dirPath:
            DIRECTORY = os.listdir(dirPath)
            if len(DIRECTORY) == 0:
                raise RuntimeError("Selected directory is empty.")

            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = []
                print()
                for num, filename in enumerate(tqdm(DIRECTORY, desc="Seperating", unit="img")):
                    if not filename.endswith((".png", ".PNG")):
                        skippedFiles += 1
                        continue
                    futures.append(executor.submit(process_sep, os.path.join(dirPath, filename), num+1, dirPath))

                with tqdm(total=len(futures), desc="Updating", unit="img") as pbar:
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            skipped = future.result()
                            skippedFiles += skipped
                            pbar.update(1)
                        except Exception as e:
                            raise RuntimeError("Error occurred while processing an image.") from e

                files_to_remove = [filename for filename in DIRECTORY if not re.match(r"\d{4}[a-zA-Z]", str(filename)[:-4])]
                with tqdm(total=len(files_to_remove), desc="Removing", unit="file") as pbar:
                    for filename in files_to_remove:
                        try:
                            os.remove(os.path.join(dirPath, filename))
                            pbar.update(1)
                        except Exception as e:
                            raise RuntimeError("Error occurred while removing a file.") from e

                result = f"Successfully split {len(DIRECTORY)} images into questions and answers.\nSkipped {skippedFiles} files."
        else:
            raise RuntimeError("No directory selected.")
    except Exception as e:
        result = f"Error occurred during image separation:\n{str(e)}"
        mb.showerror("Error", result)

    mb.showinfo("Result", result)


def process_sep(fullpath: str, num: int, dirPath: str) -> int:
    def helperSplit(image, splitPoint) -> tuple:
        width, height = image.size
        if splitPoint > height or splitPoint <= 0:
            raise ValueError("Split point out of bounds.")
        return image.crop((0, 0, width, splitPoint)), image.crop((0, splitPoint, width, height))

    try:
        img = Image.open(fullpath)
        data = pyt.image_to_data(img, output_type=pyt.Output.DICT, lang='eng', config='--psm 6')
        sz = len(data['level'])
        split = next((data['top'][i] - 10 for i in range(sz) if checkStr.lower() in str(data['text'][i]).lower()), -1)
        if split == -1:
            return 1

        question, ans = helperSplit(img, split)
        question = ImageOps.expand(question, (0, 0, 0, 15), fill="white")
        question.save(dirPath + f"{num:04}q.png", "PNG")
        ans.save(dirPath + f"{num:04}a.png", "PNG")

        return 0
    except Exception as e:
        raise RuntimeError("Error occurred while processing an image.") from e

def extractAns() -> None:
    global outfile
    if not outfile:
        mb.showinfo(
            "No Output File",
            "You have not selected an output file. To select an output file, go to settings and click the pink button that says \"Select Output File\"."
        )
        return
    DIRECTORY = filedialog.askdirectory(title="Select Extraction Folder")
    if not DIRECTORY:
        mb.showinfo("Result", "No directory selected.")
        return
    result, errors = "", []
    files = [filename for filename in os.listdir(DIRECTORY) if filename.endswith(".png") and filename[-5] == 'a']
    with tqdm(total=len(files), desc="Extracting", unit="img") as progress_bar:
        try:
            with open(outfile, "w") as out:
                for filename in files:
                    NUMBER = filename[:4]
                    try:
                        extracted_text = pyt.image_to_string(
                            os.path.join(DIRECTORY, filename),
                            lang='eng',
                            config="--psm 6"
                        )
                        out.write(f"{NUMBER}: {extracted_text.strip()[5]}\n")
                    except Exception as e:
                        errors.append(NUMBER)
                        print(f"Error occurred for file {filename}: {str(e)}")
                    progress_bar.update(1)
        except IOError as e:
            mb.showerror("File Error", f"An error occurred while writing to the output file: {str(e)}")
            return
        if showErrors:
            result = (
                f"Errors occurred at these files: {', '.join(errors) if errors else 'No Errors!'}\n"
                "All other answers have been successfully extracted."
            )
        else:
            result = "Extracted answers that were error-free."
    mb.showinfo("Result", result)

window = tk.Tk()
window.title("PNG Split (PDF -> PNG)")
window.protocol("WM_DELETE_WINDOW", exit)
button = Button(window, text="Select PDF File", command=select_file, width=15, height=1, font=("Arial", 30), bg="#89CFF0", fg="black", relief=tk.FLAT, cursor="hand2")
button.grid(row=0, column=0, columnspan=2, padx=25, pady=(25,12))

seperate_button = Button(window, text="Split Into Q/A", command=separater, width=15, height = 1, font=("Arial", 30), bg="#50C878", fg="black", relief=tk.FLAT, cursor="hand2")
seperate_button.grid(row=1, column=0, columnspan=2, padx=25, pady=(13,13))

extract_button = Button(window, text="Extract Answers", command=extractAns, width=15, height = 1, font=("Arial", 30), bg="#FFD580", fg="black", relief=tk.FLAT, cursor="hand2")
extract_button.grid(row=2, column=0, columnspan=2, padx=25, pady=(12,13))

setting_button = Button(window, text="Settings", command=show_message_box, width=15, height = 1, font=("Arial", 30), bg="#FA2A55", fg="black", relief=tk.FLAT, cursor="hand2")
setting_button.grid(row=3, column=0, columnspan=2, padx=25, pady=(12, 25))

window.mainloop()