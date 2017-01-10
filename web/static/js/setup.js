$(function () {
    'use strict';
    // text area auto grow
	autosize($('textarea'));

    // browse folder
    function browseFolder(path) {
        try {
            var Message = "\u8bf7\u9009\u62e9\u6587\u4ef6\u5939"; // 请选择文件夹
            var Shell = new ActiveXObject("Shell.Application");
            var Folder = Shell.BrowseForFolder(0, Message, 64, 17);
            //var Folder = Shell.BrowseForFolder(0, Message, 0);
            if (Folder != null) {
                Folder = Folder.items();
                Folder = Folder.item();
                Folder = Folder.Path;
                if (Folder.charAt(Folder.length - 1) != "\\") {
                    Folder = Folder + "\\";
                }
                document.getElementById(path).value = Folder;
                return Folder;
            }
        }
        catch (e) {
            alert(e.message);
        }
    }

    // page pre one
    $('.pull-right').find('#btnPrevOne').click(function(e) {
        e.preventDefault();

        var $panel = $(e.target).parents('.panel');
        if ($panel) {
            $panel.hide();
        }
        if ($panel.prev()) {
            $panel.prev().show();
        }
    });

    /*
    $('.panel').on('show.bs.collapse', function(){
        var $ps = $('.panel');
        for(var idx = 0; idx < $ps.length; idx++) {
            if (this === $ps.get(idx)) {
                var p = (idx + 1) * 100 / $ps.length ;
                $('.prog-line').width(p.toFixed(2) + '%');
            }
        }
    });
    */

    // page one : Harvest
    $('#btnOneNext').click(function(e){
        e.preventDefault();
        var pswd = $('#harvPswd').val(); 
        var user = $('#harvUser').val().trim();
        var path = $('#harvHome').val().trim();

        if (!user || !pswd || !path) {
            alert('please type all fields.');
            return false;
        }

        // check user name and password with server
        var bSucceed = false;
        $.post('/setup/harvest', {username: user, password: pswd, homepath: path}, function(data){
            if (data.status) {
                console.log("setup.harvest failed: ", data);
                setTimeout( function() {
                    alert("setup.harvest failed: " + data.message);
                }, 500);
            }
            else {
                bSucceed = true;
            }
        })
        .done(function(e){
            if (bSucceed) {
                $('#pageOne').hide();
                $('#pageTwo').show();
            }
        });
    });


    // page two: Ftp
    $('#btnTwoNext').click(function(e){
        e.preventDefault();
        var name = $('#ftpName').val();
        var pswd = $('#ftpPswd').val(); 
        var host = $('#ftpHost').val().trim();
        var user = $('#ftpUser').val().trim();
        var subp = $('#ftpSubp').val().trim();

        if (!pswd || !user || !host) {
            alert('please type all fields.');
            return false;
        }

        var ftpList = new Array();
        ftpList.push({
            'name': name,
            'host': host, 
            'username': user, 
            'password': pswd, 
            'rootpaths': subp
        });

        // check user name and password with server
        var bSucceed = false;
        $.post('/setup/ftp', {ftplist: JSON.stringify(ftpList)}, function(data){
            if (data.status) {
                console.log("setup.ftp failed: ", data);
                setTimeout( function() {
                    alert("setup.ftp failed: " + data.message);
                }, 500);
            }
            else {
                bSucceed = true;
            }
        })
        .done(function(e){
            if (bSucceed) {
                $('#pageTwo').hide();
                $('#pageThree').show();

                $('#rdtFtpSvr').empty()
                    .append('<option class="list-group-item-text">' + host + '</option>');
            }
        });
    });

    // page three: Redirect
    $('#btnThreeNext').click(function(e){
        e.preventDefault();
        var config = $('#rdtConfig').val().trim();
        var lpath = $('#rdtLpath').val().trim();
        var ftpsvr = $('#rdtFtpSvr').val().trim();

        if (!config || !lpath || !ftpsvr) {
            alert('please type all fields.');
            return false;
        }

        var bSucceed = false;
        $.post('/setup/redirect', {config: config, lpath: lpath, ftp: ftpsvr}, function(data){
            if (data.status) {
                console.log("setup.redirect failed: ", data);
                setTimeout( function() {
                    alert("setup.redirect failed: " + data.message);
                }, 500);
            }
            else {
                bSucceed = true;
            }
        })
        .done(function(e){
            if (bSucceed) {
                $('#pageThree').hide();
                $('#pageFour').show();
            }
        });
    });

    // page four: UDP
    $('#btnComplete').click(function(e){
        var udpBin = $('#udpBin').val();
        var bSucceed = false;

        $.post('/setup/environ', {udpbin: udpBin}, function(data) {
            if (data.status) {
                console.log("setup.environ failed: ", data);
                setTimeout( function() {
                    alert("setup.environ failed: " + data.message);
                }, 500);
            }
            else {
                bSucceed = true;
            }
        })
        .done(function() {
            if (bSucceed) {
                setTimeout( function() {
                    alert("Setup completed, click OK to redirect to home page.");
                    location.assign('/');
                }, 500);
            }
        });
    });
});