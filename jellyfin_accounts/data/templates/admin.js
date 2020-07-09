function getCookie(cname) {
    var name = cname + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    for(var i = 0; i <ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        } 
    }
    return "";
}
function whichTransitionEvent(){
    var t;
    var el = document.createElement('fakeelement');
    var transitions = {
      'transition':'transitionend',
      'OTransition':'oTransitionEnd',
      'MozTransition':'transitionend',
      'WebkitTransition':'webkitTransitionEnd'
    };

    for(t in transitions){
        if( el.style[t] !== undefined ){
            return transitions[t];
        };
    };
};
function toggleCSS() {
    var cssEl = document.querySelectorAll('link[rel="stylesheet"][type="text/css"]')[0];
    if (cssEl.href.includes("bs" + bsVersion + "-jf")) {
        var href = "bs" + bsVersion + ".css";
    } else {
        var href = "bs" + bsVersion + "-jf.css";
    };
    cssEl.href = href;
    document.cookie = "css=" + href;
};
var buttonWidth = 0;
var inTransition = false;
function toggleCSSAnim(el) {
    var switchToColor = window.getComputedStyle(document.body, null).backgroundColor;
    if (window.innerWidth < 1500) { 
        var radius = Math.sqrt(Math.pow(window.innerWidth, 2) + Math.pow(window.innerHeight, 2));
        var currentRadius = el.getBoundingClientRect().width / 2;
        var scale = radius / currentRadius;
        buttonWidth = window.getComputedStyle(el, null).width;
        document.body.classList.remove('smooth-transition');
        el.style.transform = 'scale(' + scale + ')';
        el.style.color = switchToColor;
        var transitionEnd = whichTransitionEvent();
        el.addEventListener(transitionEnd, function() {
            if (this.style.transform.length != 0) {
                toggleCSS();
                this.style.removeProperty('transform');
                document.body.classList.add('smooth-transition');
            };
        }, false);
    } else {
        toggleCSS();
        el.style.color = switchToColor;
    };
};
var cssFile = "{{ css_file }}";
var buttonColor = 'custom';
if (cssFile.includes('jf')) {
    buttonColor = 'rgb(255,255,255)';
} else if (cssFile.length == 7) {
    buttonColor = 'rgb(16,16,16)';
}
if (buttonColor != 'custom') {
    var fakeButton = document.createElement('i');
    fakeButton.classList.add('fa', 'fa-circle', 'circle');
    // fakeButton.style.color = buttonColor;
    // fakeButton.style.marginLeft = '2rem;'
    fakeButton.style = 'color: ' + buttonColor + '; margin-left: 0.4rem;';
    fakeButton.id = 'fakeButton';
    var switchButton = document.createElement('button');
    switchButton.classList.add('btn', 'btn-secondary');
    switchButton.textContent = 'Theme';
    switchButton.onclick = function() {
        var fb = document.getElementById('fakeButton')
        toggleCSSAnim(fb); 
    };
    var group = document.getElementById('headerButtons');
    switchButton.appendChild(fakeButton);
    group.appendChild(switchButton);
};

var bsVersion = {{ bsVersion }};
if (bsVersion == 5) {
    function createModal(id, find = false) {
        if (find) {
            return bootstrap.Modal.getInstance(document.getElementById(id));
        };
        return new bootstrap.Modal(document.getElementById(id));
    };
    function triggerTooltips() {
        document.getElementById('settingsMenu').addEventListener('shown.bs.modal', function() {
            // Hack to ensure anything dependent on checkboxes are disabled if necessary
            var checkboxes = document.getElementById('settingsMenu').querySelectorAll('input[type="checkbox"]');
            for (var i = 0; i < checkboxes.length; i++) {
                checkboxes[i].click();
                checkboxes[i].click();
            };
            // Initialize tooltips
            var to_trigger = [].slice.call(document.querySelectorAll('a[data-toggle="tooltip"]'));
            var tooltips = to_trigger.map(function(el) {
                return new bootstrap.Tooltip(el);
            });
        });
    };
} else if (bsVersion == 4) {
    let send_to_address = document.getElementById('send_to_address_enabled');
    if (send_to_address) {
        send_to_address.classList.remove('form-check-input');
    }
    function createModal(id, find = false) {
        return {
            show : function() {
                return $('#' + id).modal('show');
            },
            hide : function() {
                return $('#' + id).modal('hide');
            }
        };
    };
    function triggerTooltips() {
        $('#settingsMenu').on('shown.bs.modal', function() {
            var checkboxes = document.getElementById('settingsMenu').querySelectorAll('input[type="checkbox"]');
            for (var i = 0; i < checkboxes.length; i++) {
                checkboxes[i].click();
                checkboxes[i].click();
            };
            $("a[data-toggle='tooltip']").each(function (i, obj) {
                $(obj).tooltip();
            });
        });
    };
};
var loginModal = createModal('login');
var settingsModal = createModal('settingsMenu');
var userDefaultsModal = createModal('userDefaults');
var usersModal = createModal('users');
var restartModal = createModal('restartModal');

function parseInvite(invite, empty = false) {
    if (empty === true) {
        return ["None", "", "1"]
    } else {
        var i = ["", "", "0", invite['email']];
        i[0] = invite['code'];
        var time = ""
        if (invite['days'] != 0) {
            time += invite['days'] + 'd ';
        }
        if (invite['hours'] != 0) {
            time += invite['hours'] + 'h ';
        }
        if (invite['minutes'] != 0) {
            time += invite['minutes'] + 'm ';
        }
        i[1] = "Expires in " + time.slice(0, -1);
        return i

    }
}
function addItem(invite) {
    var links = document.getElementById('invites');
    var listItem = document.createElement('li');
    listItem.id = invite[0]
    listItem.classList.add('list-group-item', 'd-flex', 'justify-content-between', 'd-inline-block');
    var listCode = document.createElement('div');
    listCode.classList.add('d-flex', 'align-items-center', 'font-monospace');
    var codeLink = document.createElement('a');
    codeLink.setAttribute('style', 'margin-right: 0.5rem;');
    codeLink.appendChild(document.createTextNode(invite[0].replace(/-/g, '‑')));
    listCode.appendChild(codeLink);
    listItem.appendChild(listCode);
    var listRight = document.createElement('div');
    listText = document.createElement('span');
    listText.id = invite[0] + '_expiry'
    listText.setAttribute('style', 'margin-right: 1rem;');
    listText.appendChild(document.createTextNode(invite[1]));
    listRight.appendChild(listText);
    if (invite[2] == 0) {
        var inviteCode = window.location.href.replace('#', '') + 'invite/' + invite[0];
        codeLink.href = inviteCode;
        // listCode.appendChild(document.createTextNode(" "));
        var codeCopy = document.createElement('i');
        codeCopy.onclick = function(){toClipboard(inviteCode)};
        codeCopy.classList.add('fa', 'fa-clipboard', 'icon-button');
        listCode.appendChild(codeCopy);
        if (typeof(invite[3]) != 'undefined') {
            var sentTo = document.createElement('span');
            sentTo.setAttribute('style', 'color: grey; margin-left: 2%; font-style: italic; font-size: 75%;');
            if (invite[3].includes('Failed to send to')) {
                sentTo.appendChild(document.createTextNode(invite[3]));
            } else {
                sentTo.appendChild(document.createTextNode('Sent to ' + invite[3]));
            }
            listCode.appendChild(sentTo);
        };
        var listDelete = document.createElement('button');
        listDelete.onclick = function(){deleteInvite(invite[0])};
        listDelete.classList.add('btn', 'btn-outline-danger');
        listDelete.appendChild(document.createTextNode('Delete'));
        listRight.appendChild(listDelete);
    };
    listItem.appendChild(listRight);
    links.appendChild(listItem);
};
function updateInvite(invite) {
    var expiry = document.getElementById(invite[0] + '_expiry');
    expiry.textContent = invite[1];
}
function removeInvite(code) {
    var item = document.getElementById(code);
    item.parentNode.removeChild(item);
}
function generateInvites(empty = false) {
    // document.getElementById('invites').textContent = '';
    if (empty === false) {
        var req = new XMLHttpRequest();
        req.open("GET", "/getInvites", true);
        req.setRequestHeader("Authorization", "Basic " + btoa(window.token + ":"));
        req.responseType = 'json';
        req.onreadystatechange = function() {
            if (this.readyState == 4) {
                var data = this.response;
                if (data['invites'].length == 0) {
                    document.getElementById('invites').textContent = '';
                    addItem(parseInvite([], true));
                } else {
                    data['invites'].forEach(function(invite) {
                        var match = false;
                        var items = document.getElementById('invites').children;
                        for (var i = 0; i < items.length; i++) {
                            if (items[i].id == invite['code']) {
                                match = true;
                                updateInvite(parseInvite(invite));
                            };
                        };
                        if (match == false) {
                            addItem(parseInvite(invite));
                        };
                    });
                    var items = document.getElementById('invites').children;
                    for (var i = 0; i < items.length; i++) {
                        var exists = false;
                        data['invites'].forEach(function(invite) {
                            if (items[i].id == invite['code']) {
                                exists = true;
                            }
                        });
                        if (exists == false) {
                            removeInvite(items[i].id);
                        }
                    };
                };
            };
        };
        req.send();
    } else if (empty === true) {
        document.getElementById('invites').textContent = '';
        addItem(parseInvite([], true));
    };
};
function deleteInvite(code) {
    var send = JSON.stringify({ "code": code });
    var req = new XMLHttpRequest();
    req.open("POST", "/deleteInvite", true);
    req.setRequestHeader("Authorization", "Basic " + btoa(window.token + ":"));
    req.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
    req.onreadystatechange = function() {
        if (this.readyState == 4) {
            generateInvites();
        };
    };
    req.send(send);
};
function addOptions(le, sel) {
    for (v = 0; v <= le; v++) {
        var opt = document.createElement('option');
        opt.appendChild(document.createTextNode(v));
        opt.value = v;
        sel.appendChild(opt);
    }
};
function toClipboard(str) {
    const el = document.createElement('textarea');
    el.value = str;
    el.setAttribute('readOnly', '');
    el.style.position = 'absolute';
    el.style.left = '-9999px';
    document.body.appendChild(el);
    const selected =
        document.getSelection().rangeCount > 0
            ? document.getSelection().getRangeAt(0)
            : false;
    el.select();
    document.execCommand('copy');
    document.body.removeChild(el);
    if (selected) {
        document.getSelection().removeAllRanges();
        document.getSelection().addRange(selected);
    }
};

document.getElementById('inviteForm').onsubmit = function() {
    var button = document.getElementById('generateSubmit');
    button.disabled = true;
    button.innerHTML =
        '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true" style="margin-right: 0.5rem;"></span>' +
        'Loading...';
    send_object = serializeForm('inviteForm');
    console.log(send_object);
    if (document.getElementById('send_to_address') != null) {
        if (send_object['send_to_address_enabled']) {
            send_object['email'] = send_object['send_to_address'];
            delete send_object['send_to_address'];
            delete send_object['send_to_address_enabled'];
        }
    }
    var send = JSON.stringify(send_object);
    var req = new XMLHttpRequest();
    req.open("POST", "/generateInvite", true);
    req.setRequestHeader("Authorization", "Basic " + btoa(window.token + ":"));
    req.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
    req.onreadystatechange = function() {
        if (this.readyState == 4) {
            button.textContent = 'Generate';
            button.disabled = false;
            generateInvites();
        };
    };
    req.send(send);
    return false;
};
document.getElementById('loginForm').onsubmit = function() {
    window.token = "";
    var details = serializeForm('loginForm');
    var errorArea = document.getElementById('loginErrorArea');
    errorArea.textContent = '';
    var button = document.getElementById('loginSubmit');
    button.disabled = true;
    button.innerHTML =
        '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true" style="margin-right: 0.5rem;"></span>' +
        'Loading...';
    var req = new XMLHttpRequest();
    req.responseType = 'json';
    req.onreadystatechange = function() {
        if (this.readyState == 4) {
            if (this.status == 401) {
                button.disabled = false;
                button.textContent = 'Login';
                var wrongPassword = document.createElement('div');
                wrongPassword.classList.add('alert', 'alert-danger');
                wrongPassword.setAttribute('role', 'alert');
                wrongPassword.appendChild(document.createTextNode('Incorrect username or password.'));
                errorArea.appendChild(wrongPassword);
            } else {
                var data = this.response;
                window.token = data['token'];
                generateInvites();
                var interval = setInterval(function() { generateInvites(); }, 60 * 1000);
                var day = document.getElementById('days');
                addOptions(30, day);
                day.selected = "0";
                var hour = document.getElementById('hours');
                addOptions(24, hour);
                hour.selected = "0";
                var minutes = document.getElementById('minutes');
                addOptions(59, minutes);
                minutes.selected = "30";
                loginModal.hide();
            };
        };
    };
    req.open("GET", "/getToken", true);
    req.setRequestHeader("Authorization", "Basic " + btoa(details['username'] + ":" + details['password']));
    req.send();
    return false;
};
document.getElementById('openDefaultsWizard').onclick = function() {
    this.disabled = true
    this.innerHTML =
        '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true" style="margin-right: 0.5rem;"></span>' +
        'Loading...';
    var req = new XMLHttpRequest();
    req.responseType = 'json';
    req.open("GET", "/getUsers", true);
    req.setRequestHeader("Authorization", "Basic " + btoa(window.token + ":"));
    req.onreadystatechange = function() {
        if (this.readyState == 4) {
            if (this.status == 200) {
                var users = req.response['users'];
                var radioList = document.getElementById('defaultUserRadios');
                radioList.textContent = '';
                if (document.getElementById('setDefaultUser')) {
                    document.getElementById('setDefaultUser').remove();
                };
                for (var i = 0; i < users.length; i++) {
                    var user = users[i]
                    var radio = document.createElement('div');
                    radio.classList.add('radio');
                    if (i == 0) {
                        var checked = 'checked';
                    } else {
                        var checked = '';
                    };
                    radio.innerHTML =
                        '<label><input type="radio" name="defaultRadios" id="default_' +
                        user['name'] + '" style="margin-right: 1rem;"' + checked + '>' +
                        user['name'] + '</label>';
                    radioList.appendChild(radio);
                }
                var button = document.getElementById('openDefaultsWizard');
                button.disabled = false;
                button.innerHTML = 'Set new account defaults';
                var submitButton = document.getElementById('storeDefaults');
                submitButton.disabled = false;
                submitButton.textContent = 'Submit';
                if (submitButton.classList.contains('btn-success')) {
                    submitButton.classList.remove('btn-success');
                    submitButton.classList.add('btn-primary');
                } else if (submitButton.classList.contains('btn-danger')) {
                    submitButton.classList.remove('btn-danger');
                    submitButton.classList.add('btn-primary');
                };
                settingsModal.hide();
                userDefaultsModal.show();
            };
        };
    };
    req.send();
};
document.getElementById('storeDefaults').onclick = function () {
    this.disabled = true;
    this.innerHTML =
        '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true" style="margin-right: 0.5rem;"></span>' +
        'Loading...';
    var button = document.getElementById('storeDefaults');
    var radios = document.getElementsByName('defaultRadios');
    for (var i = 0; i < radios.length; i++) {
        if (radios[i].checked) {
            var data = {'username':radios[i].id.slice(8), 'homescreen':false};
            if (document.getElementById('storeDefaultHomescreen').checked) {
                data['homescreen'] = true;
            }
            var req = new XMLHttpRequest();
            req.open("POST", "/setDefaults", true);
            req.setRequestHeader("Authorization", "Basic " + btoa(window.token + ":"));
            req.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
            req.onreadystatechange = function() {
                if (this.readyState == 4) {
                    if (this.status == 200 || this.status == 204) {
                        button.textContent = 'Success';
                        if (button.classList.contains('btn-danger')) {
                            button.classList.remove('btn-danger');
                        } else if (button.classList.contains('btn-primary')) {
                            button.classList.remove('btn-primary');
                        };
                        button.classList.add('btn-success');
                        button.disabled = false;
                        setTimeout(function(){$('#userDefaults').modal('hide');}, 1000);
                    } else {
                        button.textContent = 'Failed';
                        button.classList.remove('btn-primary');
                        button.classList.add('btn-danger');
                        setTimeout(function(){
                            var button = document.getElementById('storeDefaults');
                            button.textContent = 'Submit';
                            button.classList.remove('btn-danger');
                            button.classList.add('btn-primary');
                            button.disabled = false;
                        }, 1000);
                    };
                };
            };
            req.send(JSON.stringify(data));
        };
    };
};

//             $.ajax('/setDefaults', {
//                 data : JSON.stringify(data),
//                 contentType : 'application/json',
//                 type : 'POST',
//                 xhrFields : {
//                     withCredentials: true
//                 },
//                 beforeSend : function (xhr) {
//                     xhr.setRequestHeader("Authorization", "Basic " + btoa(window.token + ":"));
//                 },
//                 success: function() {
//                     button.textContent = 'Success';
//                     if (button.classList.contains('btn-danger')) {
//                         button.classList.remove('btn-danger');
//                     } else if (button.classList.contains('btn-primary')) {
//                         button.classList.remove('btn-primary');
//                     };
//                     button.classList.add('btn-success');
//                     button.disabled = false;
//                     setTimeout(function(){$('#userDefaults').modal('hide');}, 1000);
//                 },
//                 error: function() {
//                     button.textContent = 'Failed';
//                     button.classList.remove('btn-primary');
//                     button.classList.add('btn-danger');
//                     setTimeout(function(){
//                         var button = document.getElementById('storeDefaults');
//                         button.textContent = 'Submit';
//                         button.classList.remove('btn-danger');
//                         button.classList.add('btn-primary');
//                         button.disabled = false;
//                     }, 1000);
//                 }
//             });
//         }
//     }
// };
document.getElementById('openUsers').onclick = function () {
    this.disabled = true;
    this.innerHTML =
        '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true" style="margin-right: 0.5rem;"></span>' +
        'Loading...';
    var req = new XMLHttpRequest();
    req.open("GET", "/getUsers", true);
    req.responseType = 'json';
    req.setRequestHeader("Authorization", "Basic " + btoa(window.token + ":"));
    req.onreadystatechange = function() {
        if (this.readyState == 4) {
            if (this.status == 200) {
                var list = document.getElementById('userList');
                list.textContent = '';
                if (document.getElementById('saveUsers')) {
                    document.getElementById('saveUsers').remove();
                };
                var users = req.response['users'];
                for (var i = 0; i < users.length; i++) {
                    var user = users[i]
                    var entry = document.createElement('div');
                    entry.classList.add('form-group', 'list-group-item', 'py-1');
                    entry.id = 'user_' + user['name'];
                    var label = document.createElement('label');
                    label.classList.add('d-inline-block');
                    label.setAttribute('for', 'address_' + user['email']);
                    label.appendChild(document.createTextNode(user['name']));
                    entry.appendChild(label);
                    var address = document.createElement('input');
                    address.setAttribute('type', 'email');
                    address.readOnly = true;
                    address.classList.add('form-control-plaintext', 'text-muted', 'd-inline-block');
                    //address.setAttribute('style', 'margin-left: 2%; margin-right: 2%; color: grey;');
                    address.classList.add('addressText');
                    address.id = 'address_' + user['email'];
                    if (typeof(user['email']) != 'undefined') {
                        address.value = user['email'];
                        address.setAttribute('style', 'width: auto; margin-left: 2%;');
                    };
                    var editButton = document.createElement('i');
                    editButton.classList.add('fa', 'fa-edit', 'd-inline-block', 'icon-button');
                    editButton.setAttribute('style', 'margin-left: 2%;');
                    editButton.onclick = function() {
                        this.classList.remove('fa', 'fa-edit');
                        // var input = document.createElement('input');
                        // input.setAttribute('type', 'email');
                        // input.classList.add('email-input');
                        //var addressElement = this.parentNode.getElementsByClassName('addressText')[0];
                        var addressElement = this.parentNode.getElementsByClassName('form-control-plaintext')[0];
                        addressElement.classList.remove('form-control-plaintext', 'text-muted');
                        addressElement.classList.add('form-control');
                        addressElement.readOnly = false;
                        if (addressElement.value == '') {
                        //     input.value = addressElement.textContent;
                        // } else {
                            addressElement.placeholder = 'Email Address';
                            address.setAttribute('style', 'width: auto; margin-left: 2%;');
                        };
                        // this.parentNode.replaceChild(input, addressElement);
                        if (document.getElementById('saveUsers') == null) {
                            var footer = document.getElementById('userFooter')
                            var saveUsers = document.createElement('input');
                            saveUsers.classList.add('btn', 'btn-primary');
                            saveUsers.setAttribute('type', 'button');
                            saveUsers.value = 'Save Changes';
                            saveUsers.id = 'saveUsers';
                            saveUsers.onclick = function() {
                                var send = {}
                                var entries = document.getElementById('userList').children;
                                for (var i = 0; i < entries.length; i++) {
                                    var entry = entries[i];
                                    if (typeof(entry.getElementsByTagName('input')[0]) != 'undefined') {
                                        var name = entry.id.replace(/user_/g, '')
                                        var address = entry.getElementsByTagName('input')[0].value;
                                        send[name] = address
                                    };
                                };
                                send = JSON.stringify(send);
                                var req = new XMLHttpRequest();
                                req.open("POST", "/modifyUsers", true);
                                req.setRequestHeader("Authorization", "Basic " + btoa(window.token + ":"));
                                req.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
                                req.onreadystatechange = function() {
                                    if (this.readyState == 4) {
                                        if (this.status == 200 || this.status == 204) {
                                            usersModal.hide();
                                        };
                                    };
                                };
                                req.send(send);
                            };
                            footer.appendChild(saveUsers);
                        };
                    };
                    entry.appendChild(editButton);
                    entry.appendChild(address);
                    list.appendChild(entry);
                };
                var button = document.getElementById('openUsers');
                button.disabled = false;
                button.innerHTML = 'Users <i class="fa fa-user"></i>';
                settingsModal.hide();
                usersModal.show();
            };
        }
    };
    req.send();
};

generateInvites(empty = true);
loginModal.show()

var config = {};
var modifiedConfig = {};

document.getElementById('openSettings').onclick = function () {
    restart_setting_changed = false;
    var req = new XMLHttpRequest();
    req.open("GET", "/getConfig", true);
    req.responseType = 'json';
    req.setRequestHeader("Authorization", "Basic " + btoa(window.token + ":"));
    req.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            var settingsList = document.getElementById('settingsList');
            settingsList.textContent = '';
            config = this.response;
            for (var section of Object.keys(config)) {
                var sectionCollapse = document.createElement('div');
                sectionCollapse.classList.add('collapse');
                sectionCollapse.id = section;
                
                var sectionTitle = config[section]['meta']['name'];
                var sectionDescription = config[section]['meta']['description'];
                var entryListID = section + '_entryList';
                var sectionFooter = section + '_footer';

                var innerCollapse = `
                <div class="card card-body">
                    <small class="text-muted">${sectionDescription}</small>
                    <div class="${entryListID}">
                    </div>
                </div>
                `;

                sectionCollapse.innerHTML = innerCollapse;
                
                for (var entry of Object.keys(config[section])) {
                    if (entry != 'meta') {
                        var entryName = config[section][entry]['name'];
                        var required = false;
                        if (config[section][entry]['required']) {
                            entryName += ' <sup class="text-danger">*</sup>';
                            required = true;
                        };
                        if (config[section][entry]['requires_restart']) {
                            entryName += ' <sup class="text-danger">R</sup>';
                        };
                        if (config[section][entry].hasOwnProperty('description')) {
                            var tooltip = `
                            <a class="text-muted" href="#" data-toggle="tooltip" data-placement="right" title="${config[section][entry]['description']}"><i class="fa fa-question-circle-o"></i></a>
                            `;
                            entryName += ' ';
                            entryName += tooltip;
                        };
                        var entryValue = config[section][entry]['value'];
                        var entryType = config[section][entry]['type'];
                        var entryGroup = document.createElement('div');
                        if (entryType == 'bool') {
                            entryGroup.classList.add('form-check');
                            if (entryValue.toString() == 'true') {
                                var checked = true;
                            } else {
                                var checked = false;
                            };
                            entryGroup.innerHTML = `
                            <input class="form-check-input" type="checkbox" value="" id="${section}_${entry}">
                            <label class="form-check-label" for="${section}_${entry}">${entryName}</label>
                            `;
                            entryGroup.getElementsByClassName('form-check-input')[0].required = required;
                            entryGroup.getElementsByClassName('form-check-input')[0].checked = checked;
                            entryGroup.getElementsByClassName('form-check-input')[0].onclick = function() {
                                var state = this.checked;
                                for (var sect of Object.keys(config)) {
                                    for (var ent of Object.keys(config[sect])) {
                                        if ((sect + '_' + config[sect][ent]['depends_true']) == this.id) {
                                            document.getElementById(sect + '_' + ent).disabled = !state;
                                        } else if ((sect + '_' + config[sect][ent]['depends_false']) == this.id) {
                                            document.getElementById(sect + '_' + ent).disabled = state;
                                        };
                                    };
                                };
                            };
                        } else if ((entryType == 'text') || (entryType == 'email') || (entryType == 'password') || (entryType == 'number')) {
                            entryGroup.classList.add('form-group');
                            entryGroup.innerHTML = `
                            <label for="${section}_${entry}">${entryName}</label>
                            <input type="${entryType}" class="form-control" id="${section}_${entry}" aria-describedby="${entry}" value="${entryValue}">
                            `;
                            entryGroup.getElementsByClassName('form-control')[0].required = required;
                        } else if (entryType == 'select') {
                            entryGroup.classList.add('form-group');
                            var entryOptions = config[section][entry]['options'];
                            var innerGroup = `
                            <label for="${section}_${entry}">${entryName}</label>
                            <select class="form-control" id="${section}_${entry}">
                            `;
                            for (var i = 0; i < entryOptions.length; i++) {
                                if (entryOptions[i] == entryValue) {
                                    var selected = 'selected';
                                } else {
                                    var selected = '';
                                }
                                innerGroup += `
                                <option value="${entryOptions[i]}" ${selected}>${entryOptions[i]}</option>
                                `;
                            };
                            innerGroup += '</select>';
                            entryGroup.innerHTML = innerGroup;
                            entryGroup.getElementsByClassName('form-control')[0].required = required;
                            
                        };
                        sectionCollapse.getElementsByClassName(entryListID)[0].appendChild(entryGroup);
                    };
                };
                var sectionButton = document.createElement('button');
                sectionButton.setAttribute('type', 'button');
                sectionButton.classList.add('list-group-item', 'list-group-item-action');
                sectionButton.appendChild(document.createTextNode(sectionTitle));
                sectionButton.id = section + '_button';
                sectionButton.setAttribute('data-toggle', 'collapse');
                sectionButton.setAttribute('data-target', '#' + section);
                settingsList.appendChild(sectionButton);
                settingsList.appendChild(sectionCollapse);
            };
        };
    };
    req.send();
    settingsModal.show();
};

triggerTooltips();
// 
// $('#settingsMenu').on('shown.bs.modal', function() {
//     $("a[data-toggle='tooltip']").each(function (i, obj) {
//         $(obj).tooltip();
//     });
// });
// 
function sendConfig(modalId) {
    var modal = document.getElementById(modalId);
    var send = JSON.stringify(modifiedConfig);
    var req = new XMLHttpRequest();
    req.open("POST", "/modifyConfig", true);
    req.setRequestHeader("Authorization", "Basic " + btoa(window.token + ":"));
    req.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
    req.onreadystatechange = function() {
        if (this.readyState == 4) {
            if (this.status == 200 || this.status == 204) {
                createModal(modalId, true).hide();
                if (modalId != 'settingsMenu') {
                    settingsModal.hide();
                };
            };
        };
        // fail: function(xhr, textStatus, errorThrown) {
        //     var footer = modal.getElementsByClassName('modal-dialog')[0].getElementsByClassName('modal-content')[0].getElementsByClassName('modal-footer')[0]; 
        //     var alert = document.createElement('div');
        //     alert.classList.add('alert', 'alert-danger');
        //     alert.setAttribute('role', 'alert');
        //     alert.appendChild(document.createTextNode('Error: ' + errorThrown));
        //     footer.appendChild(alert);
        // },
    };
    req.send(send);
};

document.getElementById('settingsSave').onclick = function() {
    modifiedConfig = {};
    var restart_setting_changed = false;
    var settings_changed = false;
    
    for (var section of Object.keys(config)) {
        for (var entry of Object.keys(config[section])) {
            if (entry != 'meta') {
                var entryID = section + '_' + entry;
                var el = document.getElementById(entryID);
                if (el.type == 'checkbox') {
                    var value = el.checked.toString();
                } else {
                    var value = el.value.toString();
                };
                if (value != config[section][entry]['value'].toString()) {
                    if (!modifiedConfig.hasOwnProperty(section)) {
                        modifiedConfig[section] = {};
                    };
                    modifiedConfig[section][entry] = value;
                    settings_changed = true;
                    if (config[section][entry]['requires_restart']) {
                        restart_setting_changed = true;
                    };
                };
            };
        };
    };
    // if (restart_setting_changed) {
    if (restart_setting_changed) {
        document.getElementById('applyRestarts').onclick = function(){sendConfig('restartModal');};
        settingsModal.hide();
        restartModal.show();
    } else if (settings_changed) {
        sendConfig('settingsMenu');
    } else {
        settingsModal.hide();
    };
};
