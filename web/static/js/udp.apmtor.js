/*
 * jQuery File Upload Plugin JS Example 8.9.1
 * https://github.com/blueimp/jQuery-File-Upload
 *
 * Copyright 2010, Sebastian Tschan
 * https://blueimp.net
 *
 * Licensed under the MIT license:
 * http://www.opensource.org/licenses/MIT
 */

/* global $, window */

$(function () {
    'use strict';

    /**********************************************************************************
     *  create html table column 
     **********************************************************************************/
    var createDomElement = function(patch) {
        var htmlTmpl = '<tr>        \
                <td scope="row">    \
                    <a href="#" data-toggle="modal" data-target="#idPatchDetailDlg">%pid%</a>   \
                </td>               \
                <td>%branch%</td>   \
                <td>%date%</td>     \
                <td>%projs%</td>    \
                <td>%desc%</td>     \
                <td><button type="button" class="btn btn-primary btn-block">%action%</button></td>  \
            </tr>';

        patch['action'] = patch.patch.url ? 'Download' : 'Build';
        return htmlTmpl.replace(/%(\w+)%/g, function(m, p) { return patch[p]; });
    }

    /**********************************************************************************
     *  patch list, bind button click event
     **********************************************************************************/
    $('#idPatchList').delegate("Button", "click", function(e){
        var $btn = $(e.target);
        if($btn.text() == 'Download') {
            /**
             *  download patch Button
             */
            var $row = $(this).closest("tr");
            var pid = $row.find('td:eq(0)').text().trim();
            var brn = $row.find('td:eq(1)').text().trim();
            var url = '/api/download/' + brn + '/' + pid;
                
            // id=1 : for check if file exist
            $.get(url, {type: 1}, function(data){
                console.log(data);
                if( data.status != 0 ){
                    alert('patch file not exist.');
                }
                else {
                    // download file
                    //location.assign(url);
                    window.open(url, '_blank');
                }
            });
        }
        else if ($btn.text() == 'Build') {
            /****
             *  build patch Button 
             */
            var $row = $(this).closest("tr");
            var pid = $row.find('th').eq(0).text().trim();
            var brn = $row.find('td').eq(0).text().trim();
            alert('build ' + brn + ' ' + pid);
        }

        return false;
    });

    /**********************************************************************************
     *   download patch Button
     **********************************************************************************/
    $('#idBranchPanel a').click(function(e) {
        e.preventDefault();
        var branch = $(this).find('h4').text();

        $('#idBranchPanel a').removeClass('active');
        $('#newPatchPanel').hide('slow');
        $(this).addClass('active');
        
        $.get('/api/patchs/' + branch, function(data, status){
            // sort by pid
            data.patchs.sort(function(a, b) {
                return a.pid >= b.pid;
            });
            
            $('#idPatchList').empty();
            for (var i = 0; i < data.patchs.length; i++) {
                $('#idPatchList').append(createDomElement(data.patchs[i]));
            }

            // set cookie branch
            Cookies.set('branch', branch);
        });
    });

    // trigger the default 
    $('#idBranchPanel a').eq(0).click();


    /**********************************************************************************
     *   show patch detail dialog 
     **********************************************************************************/
    $('#idPatchDetailDlg').on('show.bs.modal', function (event) {
        var parent = $(event.relatedTarget); // Button that triggered the modal
        var branch = Cookies.get('branch');
        var pid = parent.text().trim();
        var $modal = $(this);
        
        // get patch information from server
        console.log('get ' + branch + ' ' + pid);
        $.get('/api/patchs/' + branch + '/' + pid, function (data) {
            if (data.status || data.patchs.length == 0) {
                console.log(data);
                alert('Failed to get patch detail information of ' + pid);
            }
            else {
                var patch = data.patchs[0];
                //console.log(patch);
                
                $modal.find('#id-patch-projs').empty();
                for (var i = 0; i < patch['projs'].length; i++) {
                    $modal.find('#id-patch-projs').append("<span class='label label-info'>" + patch.projs[i] + "</span>");
                }

                $modal.find('#id-patch-files').empty();
                for (var i = 0; i < patch.files.length; i++) {
                    var file = patch['files'][i];
                    var li = "<li><a href='" + file.url + "'>" + file.name + "</a></li>";
                    //console.log(li);
                    $modal.find('#id-patch-files').append(li);
                }

                $modal.find('#id-patch-pid').text(pid)
                $modal.find('#id-patch-branch').text(branch);
                $modal.find('#id-patch-date').text(patch.date);
                $modal.find('#id-patch-desc').text(patch.desc);
                $modal.find('#id-patch-zip')
                    .text(patch.patch.name || 'No Patch File')
                    .attr('href', patch.patch.url || '#');
            }
        });
    });

    /**********************************************************************************
     *   create new patch Button
     **********************************************************************************/
    $('#idNewPatchSubmit').click( function(e) {
        e.preventDefault();

        if($('tr.template-upload').length) {
            alert('Please upload files first');
            return false;
        }

        if ($('#id-patch-proj').val().trim() == ""){
            alert('Please input at lease one project name');
            return false;
        }

        $('#idNewPatchBtn').prop('disabled', 'disabled');
        
        // get uploaded file list
        var fileList = $('tbody.files > tr span.name').map(function() { 
            return this.innerText;
        });
        
        var branch = $('#udpBranch').val();
        var patchFrm = new FormData($('#idNewPatchForm')[0]);
        patchFrm.append('fileList', fileList.get());

        $.ajax({
            url: '/api/patchs/new',
            type: 'POST',
            data: patchFrm,
            processData: false,
            contentType: false,
            success: function(data) {
                console.log(data);
                if (data.status == 0) {
                    //alert('Succeed to create patch ' + data.pid + ' of branch ' + data.branch)
                    $('tbody.files').empty();
                    $('#idNewPatchForm')[0].reset();
                    $('#idPatchList').append(createDomElement(data.patch));

                    // get next pid
                    $.get('/api/patchs/pid/' + branch, function(data){
                        if (data.status) {
                            console.log(data);
                            alert('get new pid error : ' + data.message);
                        }
                        else {
                            $('#patchID').val(data.pid);
                            $('#udpBranch').val(data.branch);
                            $('#fileupload').fileupload({
                                // Uncomment the following to send cross-domain cookies:
                                //xhrFields: {withCredentials: true},
                                url: '/api/upload/' + data.branch + '/' + data.pid,
                            });
                        }
                    });
                }
                else {
                    alert('Create patch failed : ' + data.message)
                }
                
                $('#idNewPatchBtn').removeAttr('disabled');
            }
        });

        return false;
    });

    /**********************************************************************************
     *  show new patch panel
     **********************************************************************************/
    $('#idNewPatchBtn').click(function(e){
        e.preventDefault();
        var $panel = $('#newPatchPanel');
        var bShowing = false;

        if ($panel.is(':hidden')) {
            bShowing = true;
        }
        
        $panel.slideToggle(function () {
            if (bShowing) {
                $.get('/api/patchs/pid/' + Cookies.get('branch'), function (data) {
                    if (data.status) {
                        console.log(data);
                        alert('get new pid error : ' + data.message);
                    } else {
                        $panel.find('#patchID').val(data.pid);
                        $panel.find('#udpBranch').val(data.branch);

                        $('#fileupload').fileupload({
                            // Uncomment the following to send cross-domain cookies:
                            //xhrFields: {withCredentials: true},
                            url: '/api/upload/' + data.branch + '/' + data.pid,
                        });
                    }
                });
            }
        });
    });

    /**********************************************************************************
     *  project list panel
     **********************************************************************************/
    $('#id-patch-proj').blur(function(e){
        var projArr = $(this).val().trim().split(';');
        if ($(this).val() == "" || projArr.length < 1) {
            return false;
        }

        var clzArray = ['label-primary', 'label-success', 'label-info', 'label-warning'];
        var $labalList = $(this).next().empty();

        //$labalList.empty()
        for(var i = 0; i < projArr.length; i++) {
            $labalList.append('<span class="label ' + clzArray[i % 4] + ' mr-5">' + projArr[i] + '</span>')
        }
    });



    /**********************************************************************************
     *  At the end : Initialize the jQuery File Upload widget:
     *********************************************************************************
    $('#fileupload').fileupload({
        // Uncomment the following to send cross-domain cookies:
        //xhrFields: {withCredentials: true},
        url: $('#fileupload').attr('action') + "?type=2"
    });

    if (window.location.hostname !== 'blueimp.github.io') {
        // Load existing files:
        $('#fileupload').addClass('fileupload-processing');
        $.ajax({
            // Uncomment the following to send cross-domain cookies:
            //xhrFields: {withCredentials: true},
            url: $('#fileupload').fileupload('option', 'url'),
            dataType: 'json',
            context: $('#fileupload')[0]
        }).always(function () {
            $(this).removeClass('fileupload-processing');
        }).done(function (result) {
            $(this).fileupload('option', 'done')
                .call(this, $.Event('done'), {result: result});
        });
    }
    */
});
