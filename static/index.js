$('input[type="file"]').change((file) => {
    console.log("Hello");
    var fileName = file.target.files[0].name;
    $(".custom-file-label")[0].innerHTML = fileName;
});
