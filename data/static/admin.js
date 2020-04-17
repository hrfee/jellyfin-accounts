function parseInvite(invite, empty = false) {
    if (empty === true) {
        return ["None", "", "1"]
    } else {
        var i = ["", "", "0"];
        i[0] = invite['code'];
        if (invite['hours'] == 0) {
            i[1] = invite['minutes'] + 'm';
        } else if (invite['minutes'] == 0) {
            i[1] = invite['hours'] + 'h';
        } else {
            i[1] = invite['hours'] + 'h ' + invite['minutes'] + 'm';
        }
        i[1] = "Expires in " + i[1] + "  ";
        return i
    }
}
function addItem(invite) {
    var links = document.getElementById('invites');
    var listItem = document.createElement('li');
    listItem.id = invite[0]
    listItem.classList.add('list-group-item', 'd-flex', 'justify-content-between', 'd-inline-block');
    var listCode = document.createElement('div');
    listCode.classList.add('d-flex', 'align-items-center', 'text-monospace');
    var codeLink = document.createElement('a');
    codeLink.setAttribute('style', 'margin-right: 2%;');
    codeLink.appendChild(document.createTextNode(invite[0].replace(/-/g, '‑')));
    listCode.appendChild(codeLink);
    listItem.appendChild(listCode);
    var listRight = document.createElement('div');
    listText = document.createElement('span');
    listText.id = invite[0] + '_expiry'
    listText.appendChild(document.createTextNode(invite[1]));
    listRight.appendChild(listText);
    if (invite[2] == 0) {    
        var inviteCode = window.location.href + 'invite/' + invite[0];
        codeLink.href = inviteCode;
        // listCode.appendChild(document.createTextNode(" "));
        var codeCopy = document.createElement('i');
        codeCopy.onclick = function(){toClipboard(inviteCode)};
        codeCopy.classList.add('fa', 'fa-clipboard');
        listCode.appendChild(codeCopy);
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
        $.ajax('/getInvites', {
            type : 'GET',
            dataType : 'json',
            contentType: 'json',
            xhrFields : {
                withCredentials: true
            },
            beforeSend : function (xhr) {
                xhr.setRequestHeader("Authorization", "Basic " + btoa(window.token + ":"));
            },
            data: { get_param: 'value' },
            complete: function(response) {
                var data = JSON.parse(response['responseText']);
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
            }
        });
    } else if (empty === true) {
        document.getElementById('invites').textContent = '';
        addItem(parseInvite([], true));
    };
};
function deleteInvite(code) {
    var send = JSON.stringify({ "code": code });
    $.ajax('/deleteInvite', {
        data : send,
        contentType : 'application/json',
        type : 'POST',
        xhrFields : {
            withCredentials: true
        },
        beforeSend : function (xhr) {
            xhr.setRequestHeader("Authorization", "Basic " + btoa(window.token + ":"));
        },
        success: function() { generateInvites(); },
    });
};
function addOptions(le, sel) {
    for (v = 0; v <= le; v++) {
        var opt = document.createElement('option');
        opt.appendChild(document.createTextNode(v))
        opt.value = v
        sel.appendChild(opt)
    }
};
function toClipboard(str) {
    const el = document.createElement('textarea'); 
    el.value = str;                                
    el.setAttribute('readonly', '');               
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
$("form#inviteForm").submit(function() {
    var send = $("form#inviteForm").serializeJSON();
    $.ajax('/generateInvite', {
        data : send,
        contentType : 'application/json',
        type : 'POST',
        xhrFields : {
            withCredentials: true
        },
        beforeSend : function (xhr) {
            xhr.setRequestHeader("Authorization", "Basic " + btoa(window.token + ":"));
        },
        success: function() { generateInvites(); },
        
    });
    return false;
});
$("form#loginForm").submit(function() {
    window.token = "";
    var details = $("form#loginForm").serializeObject();
    $.ajax('/getToken', {
        type : 'GET',
        dataType : 'json',
        contentType: 'json',
        xhrFields : {
            withCredentials: true
        },
        beforeSend : function (xhr) {
            xhr.setRequestHeader("Authorization", "Basic " + btoa(details['username'] + ":" + details['password']));
        },
        data: { get_param: 'value' },
        complete: function(data) {
            if (data['status'] == 401) {
                var formBody = document.getElementById('formBody');
                var wrongPassword = document.createElement('div');
                wrongPassword.classList.add('alert', 'alert-danger');
                wrongPassword.setAttribute('role', 'alert');
                wrongPassword.appendChild(document.createTextNode('Incorrect username or password.'));
                formBody.appendChild(wrongPassword);
            } else {
                window.token = JSON.parse(data['responseText'])['token'];
                generateInvites();
                var interval = setInterval(function() { generateInvites(); }, 60 * 1000);
                var hour = document.getElementById('hours');
                addOptions(24, hour);
                hour.selected = "0";
                var minutes = document.getElementById('minutes');
                addOptions(59, minutes);
                minutes.selected = "30";
                $('#login').modal('hide');
            }
        }
    });
    return false;
});
generateInvites(empty = true);
$("#login").modal('show');

