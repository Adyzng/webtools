 /* global $, window */

$(document).ready(function() {
    'use strict';

	// (new Date()).Format("yyyy-MM-dd hh:mm:ss.S") ==> 2006-07-02 08:09:04.423 
	// (new Date()).Format("yyyy-M-d h:m:s.S")      ==> 2006-7-2 8:9:4.18 
	Date.prototype.Format = function (fmt) {
		var o = {
				"M+": this.getMonth() + 1,
				"d+": this.getDate(),
				"h+": this.getHours(), 
				"m+": this.getMinutes(), 
				"s+": this.getSeconds(), 
				"q+": Math.floor((this.getMonth() + 3) / 3), 
				"S": this.getMilliseconds() 
			};
		if (/(y+)/.test(fmt)) 
			fmt = fmt.replace(RegExp.$1, (this.getFullYear() + "").substr(4 - RegExp.$1.length));
		for (var k in o)
			if (new RegExp("(" + k + ")").test(fmt)) 
				fmt = fmt.replace(RegExp.$1, (RegExp.$1.length == 1) ? (o[k]) : (("00" + o[k]).substr(("" + o[k]).length)));
		return fmt;
	}

	// text area auto grow
	autosize($('textarea'));

	/**********************************************************************************
     *  form reset event
     **********************************************************************************/
	$('form').on('reset', function(e){
		// update textarea height
		autosize.update($('textarea', this).val(''));
	});

	/**********************************************************************************
     *  panel expend or collapse
     **********************************************************************************/
	$('.collapse').on('show.bs.collapse', function () {
		// do something…
		$(this).prev().find('span').attr('class', 'fa fa-chevron-circle-up');
	});
	$('.collapse').on('hide.bs.collapse', function () {
		// do something…
		$(this).prev().find('span').attr('class', 'fa fa-chevron-circle-down');
	});
	
	/**********************************************************************************
     *   toolkit convert time
     **********************************************************************************/
	$('#idTimeConvertFrm .input-group-btn > button').click(function(e){
		e.preventDefault();
		var targetId = $(e.target).data('target');
		//console.log(targetId);

		// Format
		var fmt = 'yyyy-MM-dd hh:mm:ss';
		if (targetId == '#idSeconds') {
			$(targetId).val(parseInt(new Date().getTime() / 1000));
		}
		else if (targetId == '#idUTCTime'){
			var dateLocal = new Date();
			$(targetId).val(new Date(dateLocal.getTime() + dateLocal.getTimezoneOffset() * 60000 ).Format(fmt));
		}
		else if (targetId == '#idLocalTime'){
			$(targetId).val(new Date().Format(fmt));
		}
	});

    $('#idConvertBtn').click(function(e){
        e.preventDefault();
        var ms = $("#idSeconds").val().trim();
        var utcTime = $('#idUTCTime').val().trim();
        var localTime = $('#idLocalTime').val().trim();
        
		$.post('toolkit/timeconvert', {'sec' : ms, 'utc': utcTime, 'local': localTime}, function(data){
			//console.log(data);
			if (data.status == 0) {
				$("#idSeconds").val(data.sec);
				$('#idUTCTime').val(data.utc);
				$('#idLocalTime').val(data.local);
				$('#idLocalTZ').text(data.timezone);
				$('#idLocalTZ').show( "slow" );
			}
			else {
				alert('Server Error : ' + data.message);
			}
		});
    });

	/**********************************************************************************
     *  encrypt/decrypt
     **********************************************************************************/
	$('#idEncDec').click(function(e){
		e.preventDefault();
		var message = $('#idMessage').val();
		var udp_enc = $('#idUDPEnc').val();
		var base64 = $('#idBase64').val();
		var md5 = $('#idMD5').val();

		if (!(message || base64 || udp_enc)) {
			alert('Source message is empty!');
		}
		else {
			$.post('toolkit/encdec', {'source': message, 'udp': udp_enc, 'base64': base64, 'md5': ''}, function(data){
				//console.log(data);
				if (data.status == 0) {
					$("#idMessage").val(data.source);
					$("#idUDPEnc").val(data.udp);
					$("#idBase64").val(data.base64);
					$("#idMD5").val(data.md5);
					$("#idSHA1").val(data.sha1);
					$("#idSHA256").val(data.sha256);
					
					// update textarea height
					autosize.update($('textarea', '#idEncrypt'));
				}
				else {
					alert('Server Error : ' + data.message);
				}
			});
		}
	});

	/**********************************************************************************
     *  js escape/unescape
     **********************************************************************************/
	$('#idEscapeBtn').click(function(e){
		var src = $('#idStrSrc').val().trim();
		var esc = $('#idEscaped').val().trim();

		if (src == '' && esc == '') {
			alert('Input is empty');
		}
		else if (esc) {
			$('#idStrSrc').val(unescape(esc.replace(/\\/g, '%')));
		}
		else if (src) {
			var txt = escape(src.replace(/%/g, '\\'));
			$('#idEscaped').val(txt/*.replace(/%20/g, ' ')*/);
		}

		// update textarea height
		autosize.update($('textarea', '#idEscape'));
		return false;
	});

	/*********************************************************************************
	 * ftp file upload  / zTree operations
	 ********************************************************************************/
	// id of zTree
	var ID_ZTREE = {'harvest': 'treeHarvest', 'ftp': 'treeFtp'};

	// zTree initialize
	function zTreeInit() {
		// zTree custom settings
		var setting = {
			//view: { addHoverDom: addHoverTip, selectedMulti: false, showTitle: false},
			callback: { beforeExpand: zTreeGetChildrens, beforeCheck: zTreeGetChildrens, onDblClick: zTreeOnDblClick},
			check: { enable: true },
			data: { keep: { parent: true}, simpleData: { enable: true } },
		};

		// zTree initialize
		var zNodes = [ { id: 1, pId: 0, name: '/', path: '/', isParent:true, isInit:false } ];
		$.fn.zTree.init($('#' + ID_ZTREE.harvest), setting, zNodes);

		setting.check.enable = false;
		$.fn.zTree.init($('#' + ID_ZTREE.ftp), setting, zNodes);
	};

	// get child node
	function zTreeGetChildrens(treeId, treeNode) {
		if (treeId === undefined || treeNode === undefined)
			return false;
		if (treeNode.isInit || !treeNode.isParent)
			return true;
		
		var ftpRoot = $('#idFtpRoot').val().trim();
		var src = $('#' + treeId).data('src');
		if (src === 'ftp') $('#' + treeId).isLoading();

		
		$.get('/toolkit/' + src + '/redirect', {'path': treeNode.path, 'type' : 'files' }, function(data){
			var childNodes = [];
			if (data.status === 15) {
				console.log(data);
				return false;
			}

			data.files.forEach(function(ele, idx){
				var title = '';
				if (!ele.folder) {
					title = 'Modified: ' + ele.modified + ',  Size: ' + ele.size;
				}

				childNodes.push({
					id: treeNode.id + '' + idx, 
					pId: treeNode.id,
					name: ele.name, 
					path: ele.relative, 
					title: title,
					isParent: ele.folder,
					checked: treeNode.checked,
				});
			});

			var zTree = $.fn.zTree.getZTreeObj(treeId);
			if (zTree && childNodes.length){
				treeNode.isInit = true;
				zTree.addNodes(treeNode, childNodes);

				// add title
				treeNode.children.forEach(function(node) {
					if (!node.isParent) {
						$("#" + node.tId + "_a").attr('title', node.title);
					}
				});
			}
		}).always(function(e){
			if (src === 'ftp') 
				$('#' + treeId).isLoading('hide');
		});

		return true;
	};

	// traverse all checked node
	function zTreeCheckedNodes(treeObj, callback ) {
		var results = [];
		var innerCheck = function(node){
			if (!node.checked) 
				return;
			
			if( node.isParent ) {
				if (node.check_Child_State != 1) {	// 1: means part of children been checked
					results.push(node);
				}
				else {
					if (node.children)
						node.children.forEach(innerCheck);
				}
			}
			else {
				results.push(node);					// children selected
			}
		};

		treeObj.getNodes().forEach(innerCheck);
		return results;
	};

	// clean all zTree nodes
	function zTreeCleanNodes(treeId, ftpRoot) {
		var treeObj = $.fn.zTree.getZTreeObj(treeId);
		if (treeObj) {
			treeObj.getNodes().forEach(function(node){
				node.isInit = false;
				treeObj.removeChildNodes(node);
				treeObj.expandNode(node, false);

				// set new ftp root path
				if (treeId === ID_ZTREE['ftp'] && typeof(ftpRoot) !== "undefined" ) {
					node.path = ftpRoot;
				}
			});
		};
	};

	// add file time tooltip
	function addHoverTip(treeId, treeNode) {
        if (treeNode.isParent) return;
		$("#" + treeNode.tId + "_a").attr('title', treeNode.modified);
    };

	// on double click to download this file
	function zTreeOnDblClick(event, treeId, treeNode) {
		if (treeNode.isParent) return;

		var src = $('#' + treeId).data('src');
		var url = '/toolkit/' + src + '/redirect?type=download&path=' + treeNode.path;

		// download file
		window.open(url, '_blank');
	};

	/**
	 *  zTree initialize !important
	 */
	zTreeInit();

	// ftp root path change
	$('#idFtpRoot').change(function(e){
		var ftpRoot = $('#idFtpRoot').val().trim();
		zTreeCleanNodes(ID_ZTREE['ftp'], ftpRoot);
	}).change(); // called after zTreeInit

	// get tree node's children
	$('#ftpPage .fa-refresh').click( function(e){
		// sync harvest/ftp files to local to speed up expand
		var self = $(this);
		var src = self.data('src');

		if (self.data('sync')) {
			console.log('sync is onging ...');
			return false;
		}

		var stopStartSpin = function(bStart) {
			if (bStart) {
				$('#' + ID_ZTREE[src]).parent().isLoading();
			}
			else {
				$('#' + ID_ZTREE[src]).parent().isLoading('hide');
			}
		};

		// sync onging
		self.data('sync', 1);
		self.parent().attr('disabled', true);
		stopStartSpin(true);

		var ftpRoot = $('#idFtpRoot').val().trim();
		$.get('/toolkit/' + src + '/redirect', {'type' : 'sync', 'root': ftpRoot }, function(data){
			self.removeData('sync');

			if (data.status === 0) {
				zTreeCleanNodes(ID_ZTREE[src]);
			}
			else {
				alert(data.message);
				console.log(data);
			}
		}).always(function(){
			self.parent().attr('disabled', false);
			stopStartSpin(false);
		});

		return false;
	});

	// Modal showing 
	$('#idUploadModal').on('show.bs.modal', function (event) {
		if ($('#idUploadConfirm').data('uploading'))
			return;
		
		// title change
		var ftpRoot = $('#idFtpRoot').val().trim();
		$(this).find('.modal-title').text('ftp upload => ' + ftpRoot);

		var zTree = $.fn.zTree.getZTreeObj(ID_ZTREE.harvest);
		if (zTree === undefined) return false;
		var tpl = '<tr><td><i class="fa fa-clock-o"/></td><td>%PATH%</td><td/></tr>';

		// upload list
		zTreeCheckedNodes(zTree).forEach(function(node){
			$('#idUploadTable').append(tpl.replace('%PATH%', node.path));
		});
	});

	// Modal hide
	$('#idUploadModal').on('hidden.bs.modal', function(event) {
		if ($('#idUploadConfirm').data('uploading'))
			return;

		$('#idUploadTable').empty();
	});

	// Modal confirm upload
	$('#idUploadConfirm').click( function(e) {
		var $btn = $(this),
			$items = $('#idUploadTable > tr');

		if ($items === undefined || $items.length < 1)
			return;

		var toupload = [];
		$items.each(function(){
			var self = $(this);
			if (!self.data('status') ) {
				toupload.push(self);
			}
		});

		// if no items need to be upload
		if(toupload.length === 0)
			return false;
		
		var ftpRoot = $('#idFtpRoot').val().trim();
		console.log('upload to ' + ftpRoot);

		// upload function
		function svrUpload(self) {
			var path = self.children(':eq(1)').text();
			self.children(':last').text('');
			self.find('i')
				.css('color', '')
				.attr('class', 'fa fa-refresh fa-spin');
			
			$.post('/toolkit/ftp/redirect', {'type': 'upload', 'path': path, 'root': ftpRoot }, function (data) {
				if (data.status) {
					console.log('upload failed: ' + path + '; error: ' + data.message);
					self.children(':last').text('please retry');
					self.find('i')
						.css('color', 'red')
						.attr('class', 'fa fa-times');
				} else {
					self.find('i')
						.css('color', '')
						.attr('class', 'fa fa-check')
						.removeClass('fa-spin');
					self.data('status', 1)
						.children(':last').text('succeed');
				};
			})
			.fail(function (ret) {
				self.children(':last').text('please retry');
				self.find('i')
					.css('color', 'red')
					.attr('class', 'fa fa-times');
			})
			.always(function (ret) {
				if (toupload.length === 0) {
					// clean ftp tree node after upload complete
					zTreeCleanNodes(ID_ZTREE['ftp']);
					$btn.data('uploading', false);
					$btn.attr('disabled', false);
				} else {
					svrUpload(toupload.shift()); //next one
				}
			});
		};

		$btn.data('uploading', true);
		$btn.attr('disabled', true);

		// upload one by one
		svrUpload(toupload.shift());
	});

	// Modal  cancle upload
	$('#idUploadCancel').click(function(e){
		$('#idUploadModal').modal('hide');
	});	
});