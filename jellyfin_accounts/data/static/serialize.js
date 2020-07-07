function serializeForm(id) {
    var form = document.getElementById(id);
    var formData = {};
    for (var i = 0; i < form.elements.length; i++) {
        var el = form.elements[i];
        if (el.type != 'submit') {
            var name = el.name;
            if (name == '') {
                name = el.id;
            };
            switch (el.type) {
                case 'checkbox':
                    formData[name] = el.checked;
                    break;
                case 'text':
                case 'password':
                case 'select-one':
                case 'email':
                    formData[name] = el.value;
                    break;
            };
        };
    };
    return formData;
};