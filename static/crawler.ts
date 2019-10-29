/**
 * This script implements the companion for interacting with the crawler.
 */


interface XMLHttpRequest {
    url: string;
    method: string;
}

declare var _asdConfig: any;


class ASD {
    consoleArea: Element;
    progressBar: ProgressBarController;
    searchFields: Array<object>;
    termAssemblerBox: HTMLTextAreaElement;

    static usingProgressBar() {
        return _asdConfig.useProgressBar;
    }

    static parsingFields() {
        return _asdConfig.hasOwnProperty("parseFields");
    }

    static preventingLeave() {
        return !_asdConfig.hasOwnProperty("preventLeave") ||
            _asdConfig.preventLeave === true;
    }

    constructor() {
        this.consoleArea = document.querySelector('#console');
        if (ASD.parsingFields()) {
            this.searchFields = this.parseFields();
            this.termAssemblerBox = document.querySelector('#term-assemble-box');
            this.addConsoleLine(`parsed ${this.searchFields.length} search fields`);
        }
        if (!ASD.usingProgressBar()) {
            console.log("not using progress bar");
            return;
        }
        this.progressBar = new ProgressBarController("status-progress", "status-progress-description");
        this.progressBar.makeStatic();
        this.progressBar.updateLabel("pending operation...")
    }

    static disableButton() {
        document.querySelectorAll("button").forEach((button) => {
            button.style.cursor = "not-allowed";
        })
    }

    static enableButton() {
        document.querySelectorAll("button").forEach((button) => {
            button.style.cursor = "pointer";
        })
    }

    getConsoleArea = () => {
        if (this.consoleArea == null)
            this.consoleArea = document.querySelector("#console");
        return this.consoleArea;
    };

    updateTotalArticleNumber = (number) => {
        let element = document.querySelector("#status-article-total");
        element.textContent = String(number);
    };

    updateCrawledArticleNumber = (number) => {
        let element = document.querySelector("#status-article-crawled");
        element.textContent = String(number);
    };

    clearConsole = () => {
        let clearRange = document.createRange();
        clearRange.selectNodeContents(this.getConsoleArea());
        clearRange.deleteContents();
    };

    reportRequestFailure = (request: XMLHttpRequest) => {
        this.addConsoleLine("request " + `[${request.method}](${request.url})`
            + " failed with a status code " + request.status);
        console.log(request);
        this.progressBar.makeStatic();
        this.progressBar.updateLabel("internal error");
        ASD.enableButton();
    };

    fileRequest = (url, method, success, fail = null, body = null, doNotParseJson = false) => {
        let request = new XMLHttpRequest();
        request.url = url;
        request.method = method;
        let that = this;
        request.open(method, url);
        request.onreadystatechange = function () {
            if (request.readyState === 4)
                if (request.status === 200) {
                    if (doNotParseJson)
                        success(request);
                    else {
                        let response = JSON.parse(request.responseText);
                        let succeeded = response.good;
                        if (succeeded)
                            success(response.result);
                        else
                            fail(response.reason);
                    }
                } else if (fail !== null) that.reportRequestFailure(request);
                else if (fail !== null) that.reportRequestFailure(request);
        };
        if (body !== null) request.send(JSON.stringify(body));
        else request.send();
    };

    addConsoleLine = (line, doNotScrollToBottom = false) => {
        let newLine = document.createElement('p');
        newLine.textContent = line;
        this.getConsoleArea().appendChild(newLine);
        if (!doNotScrollToBottom)
            this.getConsoleArea().scrollTop = this.getConsoleArea().scrollHeight;
    };

    search = () => {
        this.progressBar.makeInfinite();
        this.progressBar.updateLabel("searching...");
        ASD.disableButton();
        let termBox = document.querySelector('#term-box');
        let term = (termBox as HTMLTextAreaElement).value;
        this.fileRequest("/command/search/", "POST",
            () => this.addConsoleLine("searching now..."),
            (error) => {
                this.addConsoleLine("searched failed: " + error);
                this.progressBar.makeStatic();
                this.progressBar.updateLabel("STATE ERROR");
                ASD.enableButton();
            },
            {term: term}
        );
        // give the program more time to initiate
        setTimeout(this.pollSearchStatus, 3000);
    };

    pollSearchStatus = () => {
        this.fileRequest("/poll/search/", "GET",
            (response) => {
                if (response.finished) {
                    this.updateTotalArticleNumber(response.result_count);
                    this.addConsoleLine(
                        "search finished, found " + response.result_count + " results");
                    this.progressBar.makeStatic();
                    this.progressBar.updateLabel("search finished");
                    ASD.enableButton();
                } else setTimeout(this.pollSearchStatus, 1000);
            },
            (error) => {
                this.addConsoleLine(`search failed: ${error}`);
                this.progressBar.makeStatic();
                this.progressBar.updateLabel("SEARCH FAILED");
                ASD.enableButton();
                // asd.addConsoleLine("no search status available: " + error);
                // setTimeout(this.pollSearchStatus, 1000);
            }
        );
    };

    parseYearRange = () => {
        let yearStartElement = document.querySelector("#year-from") as HTMLInputElement;
        let yearEndElement = document.querySelector("#year-to") as HTMLInputElement;
        let yearStart = parseInt(yearStartElement.value);
        let yearEnd = parseInt(yearEndElement.value);
        if (isNaN(yearStart) || isNaN(yearEnd))
            return null;
        return {yearStart: yearStart, yearEnd: yearEnd};
    };

    crawlAll = () => {
        let yearRange = this.parseYearRange();
        if (yearRange === null)
            this.crawl(0, 0, 0, 0);
        else
            this.crawl(0, 0, yearRange.yearStart, yearRange.yearEnd);
    };

    parseCrawlRange = () => {
        let crawlStartElement = document.querySelector("#crawl-from") as HTMLInputElement;
        let crawlEndElement = document.querySelector("#crawl-to") as HTMLInputElement;
        let crawlStart = parseInt(crawlStartElement.value);
        let crawlEnd = parseInt(crawlEndElement.value);
        if (isNaN(crawlStart) || isNaN(crawlEnd))
            return null;
        return {start: crawlStart, end: crawlEnd};
    };

    crawlPartially = () => {
        let yearRange = this.parseYearRange();
        let crawlRange = this.parseCrawlRange();
        if (yearRange == null) {
            if (crawlRange == null)
                this.crawl(0, 0, 0, 0);
            else
                this.crawl(crawlRange.start, crawlRange.end, 0, 0);
        } else {
            if (crawlRange == null)
                this.crawl(0, 0, yearRange.yearStart, yearRange.yearEnd);
            else
                this.crawl(crawlRange.start, crawlRange.end, yearRange.yearStart, yearRange.yearEnd);
        }
    };

    crawl = (start, end, year_start = 0, year_end = 0) => {
        this.fileRequest("/command/crawl/", "POST",
            () => this.addConsoleLine("crawling now..."),
            (error) => {
                this.addConsoleLine("cannot start crawling: " + error);
                ASD.enableButton();
                this.progressBar.makeStatic();
                this.progressBar.updateLabel("STATE ERROR");
            },
            {start: start, end: end, year_start: year_start, year_end: year_end}
        );
        this.progressBar.makeInfinite();
        this.progressBar.updateLabel("crawling...");
        ASD.disableButton();
        setTimeout(this.pollCrawlStatus, 3000);
    };

    copyTermToClipboard = (term: string) => {
        navigator.clipboard.writeText(term).then(() => {
            this.addConsoleLine(`copied term to clipboard: ${term}`);
        }).catch(() => {
            this.addConsoleLine(`unable to copy the term to clipboard, consider copying manually or use "USE SESSION"`);
        })
    };

    dropSession = (sessionId: string) => {
        let result = confirm(`You are dropping session(id="${sessionId}").\n` +
            `Once the session is deleted you will have to re-crawl the next time.\n` +
            `Proceed?`).valueOf();
        if (result == false) {
            this.addConsoleLine("user cancelled the dropping operation");
            return;
        }

        this.addConsoleLine(
            `requesting to drop collection (id=${sessionId})...`);
        this.fileRequest("/command/dropSession/", "POST",
            (response) => {
                this.addConsoleLine(`dropped collection (id=${response.id}, term="${response.term}")`);
                window.setTimeout(() => {
                    this.removeSessionElement(sessionId);
                }, 500);
            },
            (reason) => {
                this.addConsoleLine(`cannot drop collection: ${reason}`);
            },
            {sessionId: sessionId}
        );
    };

    removeSessionElement = (sessionId: string) => {
        let sessionElement = document.querySelector(`div[_session_id="${sessionId}"]`);
        if (sessionElement === null) {
            this.addConsoleLine(`cannot remove session element: no such session with id=${sessionId}`);
            return;
        }
        sessionElement.remove();
    };

    useSession = (sessionId: string) => {
        this.addConsoleLine(`opening crawler using session(id=${sessionId})`);
        window.open(`/?sessionId=${sessionId}`, "_blank");
    };

    pollCrawlStatus = () => {
        this.fileRequest("/poll/crawl/", "GET",
            (response) => {
                if (response.finished !== -1) {  // not done yet
                    // this.addConsoleLine("finished " + response.finished + " entries");
                    this.updateCrawledArticleNumber(response.finished);
                    this.progressBar.makeFinite(response.finished / response.total * 100);
                    setTimeout(this.pollCrawlStatus, 1000);
                } else {
                    this.progressBar.makeFinite(100);
                    this.progressBar.updateLabel("CRAWLING FINISHED");
                    ASD.enableButton();
                    this.addConsoleLine("crawling finished");
                }
            },
            (error) => {
                asd.addConsoleLine(`cannot poll crawl status: ${error}`);
                asd.progressBar.makeStatic();
                asd.progressBar.updateLabel("CRAWL FAILED");
                ASD.enableButton();
                // setTimeout(this.pollCrawlStatus, 1000);
            }
        );
    };

    getFilenameIndicator = () => {
        return document.querySelector("#crawler-output-file");
    };

    updateFilenameIndicator = (filename: string) => {
        this.getFilenameIndicator().textContent = filename;
    };

    requestOpenFile = () => {
        this.fileRequest("/command/requestOpenFile/", "GET",
            (response) => {
                let selectedFile: string = response.file_name;
                this.addConsoleLine("selected file: " + response.full_path);
                this.updateFilenameIndicator(selectedFile);
            },
            (reason) => {
                this.addConsoleLine("cannot select file: " + reason);
            }
        );
    };

    reset = () => {
        this.fileRequest("/command/reset/", "GET",
            (response) => {
                this.clearConsole();
                this.updateCrawledArticleNumber("N/A");
                this.updateTotalArticleNumber("N/A");
                ASD.enableButton();
                this.progressBar.makeStatic();
                this.progressBar.updateLabel("PENDING OPERATION");
                this.addConsoleLine("new session is ready");
            }, (error) => {
                this.addConsoleLine("cannot reset session: " + error);
                alert("cannot reset session: " + error);
            })
    };

    export = (sessionId, exportScript) => {
        this.fileRequest("/command/export/", "POST",
            (response) => {
                this.addConsoleLine(`exporting session(id=${sessionId} with ` +
                    `export script(name=${exportScript})...`);
                this.addConsoleLine("please pay attention to the output in the console and try not to run too many export at the same time");
            },
            (error) => {
                this.addConsoleLine(`failed to export session` +
                    `(id=${sessionId} with ` +
                    `export script(name=${exportScript})`);
                this.addConsoleLine(`error says: ${error}`);
            },
            {session_id: sessionId, export_script: exportScript})
    };

    exportWrapper = (event) => {
        console.log("clicked");
        if (event.currentTarget.tagName == "BUTTON") {
            let labelElement = event.currentTarget;
            let sessionId = labelElement.getAttribute("id").substring(6);
            let exportScript = (document.getElementById(`session-select-${sessionId}`) as HTMLSelectElement).value;
            asd.export(sessionId, exportScript);
            event.preventDefault();
            event.stopPropagation();
            event.stopImmediatePropagation();
        }
    };

    parseFields = () => {
        let availableFields = [];
        for (let field_name in _asdConfig.availableFields) {
            if (!_asdConfig.availableFields.hasOwnProperty(field_name))
                continue;
            let field_explanation = _asdConfig.availableFields[field_name];
            availableFields.push({name: field_name, explanation: field_explanation});
        }
        return availableFields;
    };

    insertTextToTermAssembler = (text: string) => {
        let textArea = this.termAssemblerBox;
        let scrollPosition = textArea.scrollTop;
        let caretPosition = textArea.selectionStart;

        let front = (textArea.value).substring(0, caretPosition);
        let back = (textArea.value).substring(textArea.selectionEnd, textArea.value.length);
        textArea.value = front + text + back;
        caretPosition = caretPosition + text.length;
        textArea.selectionStart = caretPosition;
        textArea.selectionEnd = caretPosition;
        textArea.focus();
        textArea.scrollTop = scrollPosition;
    };

    addTerm = (term: string) => {
        this.insertTextToTermAssembler(`(${term}=())`);
        this.termAssemblerBox.selectionEnd -= 2;
    };

    addNot = () => {
        this.insertTextToTermAssembler("NOT ");
    };

    addOr = () => {
        this.insertTextToTermAssembler(" OR ");
    };

    addAnd = () => {
        this.insertTextToTermAssembler(" AND ");
    };

    addConditionGroup = () => {
        this.insertTextToTermAssembler("()");
        this.termAssemblerBox.selectionEnd -= 1;
    };

    copyAssembledTermToClipboard = () => {
        navigator.clipboard.writeText(this.termAssemblerBox.value);
    };

    addRangeTerm = () => {
        let from = (document.querySelector('#term-range-from') as HTMLInputElement).value;
        let to = (document.querySelector('#term-range-to') as HTMLInputElement).value;
        this.insertTextToTermAssembler(`${from}-${to}`)
    };

    addStartingWithTerm = () => {
        let startingWith =
            (document.querySelector('#term-starting-with') as HTMLInputElement).value;
        this.insertTextToTermAssembler(`${startingWith}*`);
    };

    addEndingWithTerm = () => {
        let endingWith =
            (document.querySelector('#term-ending-with') as HTMLInputElement).value;
        this.insertTextToTermAssembler(`*${endingWith}`);
    };
}


class ProgressBarController {
    progressBar: HTMLProgressElement;
    progressBarLabel: HTMLElement;

    constructor(progressBarId: string, progressBarLabelId: string) {
        this.progressBar = document.querySelector(`#${progressBarId}`);
        this.progressBarLabel = document.querySelector(`#${progressBarLabelId}`);
        if (this.progressBar === null || this.progressBarLabel === null)
            throw new Error("invalid progress bar or progress bar label ID");
    }

    makeStatic() {
        this.progressBar.setAttribute("max", "100");
        this.progressBar.setAttribute("value", "0");
        // this.progressBar.max = 100;
        // this.progressBar.value = 0;
    }

    makeInfinite() {
        this.progressBar.removeAttribute("max");
        this.progressBar.removeAttribute("value");
    }

    makeFinite(value: number) {
        this.progressBar.setAttribute("max", "100");
        this.progressBar.setAttribute("value", `${value}`)
    }

    updateLabel(message: string) {
        this.progressBarLabel.textContent = message;
    }
}

let asd: ASD = null;

window.addEventListener("load", function () {
    console.log("we're here!");

    if (ASD.preventingLeave()) {
        window.addEventListener("beforeunload", (e) => {
            let message = "Make sure before you add";
            let ee = e || window.event;

            // For IE and Firefox
            if (ee) {
                ee.returnValue = message;
            }

            // For Safari
            return message;
        });
    }

    // if (ASD.parsingFields()) return;
    asd = new ASD();

    window.setInterval(function () {
        // pull new logs
        asd.fileRequest("/poll/log/", "GET", (response) => {
            response.new_logs.forEach((log) => {
                console.log(log);
                asd.addConsoleLine(log);
            })
        });
    }, 1000);

    // bind export buttons
    document.querySelectorAll("button.session-export-button").forEach(
        (label) => {
            label.addEventListener("click", asd.exportWrapper);
        });
});
