function addItem(invite) {
    var links = document.getElementById('invites');
    var listItem = document.createElement('li');
    listItem.classList.add('list-group-item');
    listItem.classList.add('align-middle');
    var listCode = document.createElement('div');
    listCode.classList.add('float-left');
    var codeLink = document.createElement('a');
    codeLink.appendChild(document.createTextNode(invite[0]));
    listCode.appendChild(codeLink);
    listItem.appendChild(listCode);
    var listRight = document.createElement('div');
    listRight.classList.add('float-right');
    listRight.appendChild(document.createTextNode(invite[1]));
    if (invite[2] == 0) {    
        var inviteCode = window.location.href + 'invite/' + invite[0];
        codeLink.href = inviteCode;
        listCode.appendChild(document.createTextNode(" "));
        var codeCopy = document.createElement('i');
        codeCopy.onclick = function(){toClipboard(inviteCode)};
        codeCopy.classList.add('fa');
        codeCopy.classList.add('fa-clipboard');
        listCode.appendChild(codeCopy);
        var listDelete = document.createElement('button');
        listDelete.onclick = function(){deleteInvite(invite[0])};
        listDelete.classList.add('btn');
        listDelete.classList.add('btn-outline-danger');
        listDelete.appendChild(document.createTextNode('Delete'));
        listRight.appendChild(listDelete);
    };
    listItem.appendChild(listRight);
    links.appendChild(listItem);
};
function generateInvites(empty = false) {
    document.getElementById('invites').textContent = '';
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
                    addItem(["None", "", "1"]);
                } else {
                    data['invites'].forEach(function(item) {
                        var i = ["", "", "0"];
                        i[0] = item['code'];
                        if (item['hours'] == 0) {
                            i[1] = item['minutes'] + 'm';
                        } else if (item['minutes'] == 0) {
                            i[1] = item['hours'] + 'h';
                        } else {
                            i[1] = item['hours'] + 'h ' + item['minutes'] + 'm';
                        }
                        i[1] = "Expires in " + i[1] + "  ";
                        addItem(i)
                    });
                }
            }
        });
    } else if (empty === true) {
        addItem(["None", "", "1"]);
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
                wrongPassword.classList.add('alert');
                wrongPassword.classList.add('alert-danger');
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

