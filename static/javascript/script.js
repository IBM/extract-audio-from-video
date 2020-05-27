const uploading = document.getElementById("uploading");
const error = document.getElementById("error");
const uploaded = document.getElementById("uploaded");
const refresh = document.getElementById("refresh");
const refresh2 = document.getElementById("refresh2");
const tableRef = document.getElementById("table").getElementsByTagName('tbody')[0];
const tableRef2 = document.getElementById("table2").getElementsByTagName('tbody')[0];
const table = document.getElementById("table");
const table2 = document.getElementById("table2");
const audio = document.getElementById("audio");
const converting = document.getElementById("converting");
const converted = document.getElementById("converted");
const clickBtn1 = document.getElementById("clickBtn1");
const clickBtn2 = document.getElementById("clickBtn2");
const cosNotify = document.getElementById("cosNotify");
const toast = document.getElementById("toast");
const convertButton = document.getElementById("convertButton");
const showModal = document.getElementById("showModal");

$(document).ready(function() {
    uploaded.style.display = "none";
    error.style.display = "none";
    uploading.style.display = "none";
    refresh.style.display = "none";
    refresh2.style.display = "none";
    table.style.display = "none";
    table2.style.display = "none";
    audio.style.display = "none";
    converting.style.display = "none";
    converted.style.display = "none";
    toast.style.display = "none";
    convertButton.style.display = "none";

    getCOSCredentials();

    if (isEmpty($('#myFiles'))) {

    }
    clickBtn1.click()
    clickBtn2.click()
});

async function getCOSCredentials() {
    await fetch('/initCOS').then(async(response) => {
        data = await response.json();

        temp = data.message.split(' ');

        if (temp[temp.length - 1] == "found!") {
            cosNotify.innerHTML = " ";
            cosNotify.innerHTML = temp[0] + ' ' + temp[1] + ' ' + "linked.";
            toast.style.display = "block";
        } else {
            cosNotify.innerHTML = " ";
            cosNotify.innerHTML = data.message;
            toast.style.display = "block";
        }

        if (data.message == " 'bucket_name'") {
            showModal.click();
            cosNotify.innerHTML = " ";
            cosNotify.innerHTML = "Object Storage Bucket NOT Specified!, Refresh the page to configure.";
            toast.style.display = "block";
        } else
            clickBtn2.click();

    });
}

function isEmpty(el) {
    return !$.trim(el.html())
}

$('#Upload').on('click', function() {
    uploaded.style.display = "none";
    uploading.style.display = "block";
    if (isEmpty($('#myFiles'))) {
        uploading.style.display = "none";
        error.style.display = "block";
    } else {
        error.style.display = "none";
        $.ajax({
            url: '/uploader',
            type: 'POST',
            data: new FormData($('form')[0]),
            dataType: 'json',
            cache: false,
            contentType: false,
            processData: false,
            success: function(response) {

                if (response.message != 0) {
                    uploading.style.display = "none";
                    uploaded.style.display = "block";
                    clickBtn1.click();
                } else {
                    error.style.display = "block";

                }
            },
            error: function() {
                error.style.display = "block";
            }
        });
    }

});

async function setupCOS() {
    setTimeout(function() {
        let bkt = { bucket_name: document.getElementById('bucket-name-setup').value };
        let formData = new FormData();
        formData.append("bkt", JSON.stringify(bkt));

        $.ajax({
            url: '/COSBucket',
            type: 'POST',
            data: formData,
            cache: false,
            contentType: false,
            processData: false,
            success: function(myData) {
                if (myData.flag == 0)
                    location.reload();
            },
            error: function() {
                error2.style.display = "block";
            }
        });
    }, 1000);
}

async function getUploadedFiles() {

    convertButton.style.display = "none";
    tableRef.innerHTML = " ";
    refresh.style.display = "block";
    await fetch(`/getVideoFiles`).then(async(response) => {
        data = await response.json();
        data.forEach(element => {
            // Insert a row in the table at the last row
            var newRow = tableRef.insertRow();

            // Insert a cell in the row at index 0
            var newCell = newRow.insertCell(0);
            var newCell2 = newRow.insertCell(1);
            var newCell3 = newRow.insertCell(2);
            var newCell4 = newRow.insertCell(3);

            fileFormat = element.videoFile.split('.')[1];

            // Append a text node to the cell
            var newText = document.createTextNode(element.videoFile.split('/')[1]);
            var newText2 = document.createTextNode(element.fileSize);
            var newText3 = document.createTextNode(fileFormat);
            var newText4 = document.createTextNode(fileFormat);

            newCell.appendChild(newText);
            newCell2.appendChild(newText2);
            newCell3.appendChild(newText3);
            newCell4.appendChild(newText4);

            newCell4.innerHTML = "";
            newCell4.innerHTML = `<button class="bx--btn bx--btn--ghost bx--btn--sm" onclick='deleteUploadedFile("${ element.videoFile }", "video")' type="button"> \
                            <svg focusable="false" preserveAspectRatio="xMidYMid meet" style="will-change: transform;" \
                                xmlns="http://www.w3.org/2000/svg" class="bx--btn__icon" width="16" height="16" \
                                viewBox="0 0 32 32" aria-hidden="true"> \
                                <path d="M25.7,9.3l-7-7A.91.91,0,0,0,18,2H8A2,2,0,0,0,6,4V28a2,2,0,0,0,2,2H24a2,2,0,0,0,2-2V10A.91.91,0,0,0,25.7,9.3ZM18,4.4,23.6,10H18ZM24,28H8V4h8v6a2,2,0,0,0,2,2h6Z">\
                                </path><path d="M11 19H21V21H11z"></path> </svg> </button>`;

        });
        table.style.display = "block";
        refresh.style.display = "none";
    });

    var x = document.getElementById("table").rows.length;
    if (x > 1)
        convertButton.style.display = "block";
    else
        table.style.display = "none";
}

async function convert() {
    converting.style.display = "block";
    converted.style.display = "none";
    await fetch(`/convert`).then(async(response) => {
        data = await response.json();
        console.log(data);
        if (data.flag == 0) {
            converting.style.display = "none";
            converted.style.display = "block";
            clickBtn2.click();
        } else if (data.flag == 1) {

        }
    });
}

async function getConvertedFiles() {
    tableRef2.innerHTML = " ";
    refresh2.style.display = "block";
    await fetch('/getAudioFiles').then(async(response) => {
        audio.style.display = "block";
        data = await response.json();
        data.forEach(element => {
            audioPlayer = '<br/><a><audio controls> <source src="static/' +
                element.audioFile + '" type="audio/flac"> Your browser does not support the audio element. </audio></a>';
            // Insert a row in the table at the last row
            var newRow = tableRef2.insertRow();

            // Insert a cell in the row at index 0
            var newCell = newRow.insertCell(0);
            var newCell2 = newRow.insertCell(1);
            var newCell3 = newRow.insertCell(2);
            var newCell4 = newRow.insertCell(3);

            fileFormat = element.audioFile.split('.')[1];

            // Append a text node to the cell
            var newText = document.createTextNode(element.audioFile.split('/')[1]);
            var newText2 = document.createTextNode(element.fileSize);
            var newText3 = document.createTextNode(fileFormat);
            var newText4 = document.createTextNode(fileFormat);

            newCell.appendChild(newText);
            newCell2.appendChild(newText2);
            newCell3.appendChild(newText3);
            newCell4.appendChild(newText4);

            newCell.innerHTML += audioPlayer;

            newCell4.innerHTML = "";
            newCell4.innerHTML = `<button class="bx--btn bx--btn--ghost bx--btn--sm" onclick='deleteUploadedFile("${ element.audioFile }", "audio")' type="button"> \
                            <svg focusable="false" preserveAspectRatio="xMidYMid meet" style="will-change: transform;" \
                                xmlns="http://www.w3.org/2000/svg" class="bx--btn__icon" width="16" height="16" \
                                viewBox="0 0 32 32" aria-hidden="true"> \
                                <path d="M25.7,9.3l-7-7A.91.91,0,0,0,18,2H8A2,2,0,0,0,6,4V28a2,2,0,0,0,2,2H24a2,2,0,0,0,2-2V10A.91.91,0,0,0,25.7,9.3ZM18,4.4,23.6,10H18ZM24,28H8V4h8v6a2,2,0,0,0,2,2h6Z">\
                                </path><path d="M11 19H21V21H11z"></path> </svg> </button>`;


        });
        table2.style.display = "block";
        refresh2.style.display = "none";
    });
    var x = document.getElementById("table2").rows.length;
    if (x > 1)
        table2.style.display = "block";
    else
        table2.style.display = "none";
}

async function deleteUploadedFile(fileName, fileType) {
    console.log(fileName, fileType);

    await fetch(`/deleteUploadedFile?fileName=${fileName}&fileType=${fileType}`).then(async(response) => {
        data = await response.json();
        if (data.flag == 0) {
            if (fileType == 'video')
                clickBtn1.click();
            if (fileType == 'audio')
                clickBtn2.click();
        } else if (data.flag == 1) {

        }
    });
}