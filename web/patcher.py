# coding: utf-8
"""
restful api for creating path
"""

import os

from flask import Flask, Blueprint, jsonify, request, send_from_directory, url_for
from werkzeug import secure_filename

from web.model import BranchModel, PatchModel
from web.helper import init_logger, ReplyJson, ErrorCode
from web.settings import ENVIRONS


############################################################################################
# file formater

class FileFormater():
    def __init__(self, name, brn=None, size=0, pid=None, type=None, tid=0, not_allowed_msg=''):
        self.type = type
        self.size = size
        self.name = os.path.basename(name)
        self.not_allowed_msg = not_allowed_msg
        self.thumbnail_url = ""
        self.delete_type = "DELETE"
        if brn and pid:
            if tid:
                self.url = "api/download/%s/%s/%s?type=%u" % (brn, pid, name, tid)
                self.delete_url = "api/delete/%s/%s/%s?type=%u" % (brn, pid, name, tid)
            else:
                self.url = "api/download/%s/%s/%s" % (brn, pid, name)
                self.delete_url = "api/delete/%s/%s/%s" % (brn, pid, name)
        else:
            self.url = ""
            self.delete_url = ""

    def is_image(self):
        fileName, fileExtension = os.path.splitext(self.name.lower())
        if fileExtension in ['.jpg', '.png', '.jpeg', '.bmp']:
            return True
        return False

    def get_file(self):
        if self.type != None:
            # POST an image
            if self.type.startswith('image'):
                return {"name": self.name,
                        "type": self.type,
                        "size": self.size, 
                        "url": self.url, 
                        "thumbnailUrl": self.thumbnail_url,
                        "deleteUrl": self.delete_url, 
                        "deleteType": self.delete_type,}
            
            # POST an normal file
            elif self.not_allowed_msg == '':
                return {"name": self.name,
                        "type": self.type,
                        "size": self.size, 
                        "url": self.url, 
                        "deleteUrl": self.delete_url, 
                        "deleteType": self.delete_type,}

            # File type is not allowed
            else:
                return {"error": self.not_allowed_msg,
                        "name": self.name,
                        "type": self.type,
                        "size": self.size,}

        # GET image from disk
        elif self.is_image():
            return {"name": self.name,
                    "size": self.size, 
                    "url": self.url, 
                    "thumbnailUrl": self.thumbnail_url,
                    "deleteUrl": self.delete_url, 
                    "deleteType": self.delete_type,}
        
        # GET normal file from disk
        else:
            return {"name": self.name,
                    "size": self.size, 
                    "url": self.url, 
                    "deleteUrl": self.delete_url, 
                    "deleteType": self.delete_type,}

    

############################################################################################
# helper 

UPLOAD_FOLDER = os.path.abspath(ENVIRONS['webstore'])
DENIED_EXTENSIONS = set(['exe', 'dll', 'sys'])
IGNORED_FILES = set(['.gitignore'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] not in DENIED_EXTENSIONS

def file_folder(brn, pid, patchfile=False):
    if patchfile:
        full_path = os.path.join(UPLOAD_FOLDER, brn, pid)
    else:
        full_path = os.path.join(UPLOAD_FOLDER, brn, pid, 'new')
    if not os.path.exists(full_path):
        os.makedirs(full_path)
    return full_path


def get_patch_file(brn, pid):
    p_path = os.path.join(UPLOAD_FOLDER, brn, pid, pid + '.zip')
    if os.path.exists(p_path):
        return p_path
    else:
        return None

def patch_model_2_json(brn, patch):
    '''convert patch model to json object'''
    if not isinstance(patch, PatchModel):
        raise TypeError('patch should be an instance object of PatchModel')
    #p_url = url_for('.download_files', brn=brn, pid=patch.pid, type=0)
    p_url = '' if not get_patch_file(brn, patch.pid) else '/api/download/%s/%s' % (brn, patch.pid)
    p_json = {
        'branch': brn,
        'pid'   : patch.pid,
        'date'  : patch.pdate,
        'desc'  : patch.pdesc,
        'projs' : patch.pproj.split(';'),
        'files' : [],
        'patch' : { 'name' : '%s.zip' % patch.pid, 'url': p_url },
    }

    br_store = file_folder(brn, patch.pid)
    for fi in [f for f in os.listdir(br_store) if os.path.isfile(os.path.join(br_store, f)) and f not in IGNORED_FILES]:
        fobj = FileFormater(name=fi, brn=brn, pid=patch.pid)
        p_json['files'].append( {'name': fobj.name, 'url': fobj.url} )
    return p_json

def patch_json_2_model(bid, p_json):
    '''convert json patch to patch model'''
    if not isinstance(p_json, dict):
        raise TypeError('p_json should be an instance dict')

    p_json['bid'] = bid
    return PatchModel(p_json)


############################################################################################
#  Blueprint for REST api

class PatchMaker(object):
    # Blueprint instance
    api = Blueprint('RESTAPI', __name__)
    log = init_logger()

    # register in Flask application
    @classmethod
    def register(clz, app):
        if not isinstance(app, Flask):
            raise TypeError('app should be an instance of `flask.Flask`')
        else:
            app.register_blueprint(clz.api, url_prefix='/api')
    
    @staticmethod
    @api.route('/branchs', methods=['GET'])
    @api.route('/branchs/<string:brn>', methods=['GET'])
    def query_branchs(brn=None):
        '''
        <>/api/branchs/v5
        <>/api/branchs/v6u1
        '''
        PatchMaker.log.info('get branch : %s', brn)
        brs = BranchModel.fetch(branch=brn) if brn else BranchModel.fetch_all()
        br_key = BranchModel.COLUMN.split(',')

        brs_list = [dict([(k, v) for (k, v) in zip(br_key, br.value)]) for br in brs]
        sorted(brs_list, key=lambda br: br.branch) # sort by branch name
        return jsonify(ReplyJson(ErrorCode.ERR_SUCCESS, branchs=brs_list))


    @staticmethod 
    @api.route('/patchs/<string:brn>', methods=['GET'])
    @api.route('/patchs/<string:brn>/<string:pid>', methods=['GET'])
    def query_patchs(brn, pid=None):
        '''
        <>/api/patchs/v5
        <>/api/patchs/v5/P00001
        '''
        PatchMaker.log.info("%s get patch: brn=%s, pid=%s", request.remote_addr, brn, pid)
        branch_obj = BranchModel.get_branch(brn)

        if branch_obj is not None:
            result = [patch_model_2_json(brn, p) for p in PatchModel.fetch(pid=pid, bid=branch_obj.id)]
            if len(result) == 0:
                status = ErrorCode.ERR_PID_NOT_VALID
            else:
                status = ErrorCode.ERR_SUCCESS
        else:
            result = []
            status = ErrorCode.ERR_BID_NOT_VALID
        
        sorted(result, key=lambda ph: ph['pid'])
        return jsonify(ReplyJson(status, patchs=result))


    @staticmethod
    @api.route('/patchs/pid/<string:brn>', methods=['GET'])
    def next_pid(brn):
        '''
        get next pid of branch : brn
        <>/api/patchs/pid/v5
        '''
        #brn = request.values.get('branch', None)
        branch = BranchModel.get_branch(brn)
        if branch is None:
            newid = None
            status = ErrorCode.ERR_BID_NOT_VALID
        else:
            newid = branch.next_pid()
            status = ErrorCode.ERR_SUCCESS
        
        PatchMaker.log.info('next patch id : %s for %s', newid, brn)
        return jsonify(ReplyJson(status, branch=brn, pid=newid))


    @staticmethod	
    @api.route('/patchs/new', methods=['POST'])
    def new_patchs():
        ''''''
        pid = request.form.get('patchID', None)
        brn = request.form.get('branchID', None)
        branch = BranchModel.get_branch(brn)
        
        p_json = None
        status = ErrorCode.ERR_SUCCESS

        if branch:
            patch = patch_json_2_model(branch.id, {
                'pid' : pid,
                'desc' : request.form.get('patchDesc', ''),
                'projs' : request.form.get('patchProj', ''),
                'files' : request.form.get('fileList', ''),
            })

            p_json = patch_model_2_json(brn, patch)
            status = ErrorCode.ERR_SUCCESS if 1 == patch.insert() else ErrorCode.ERR_PATCH_CREATE
        else:
            status = ErrorCode.ERR_BID_NOT_VALID
        
        PatchMaker.log.info("new patch = %s, branch = %s, status = %u", pid, brn, status)
        return jsonify(ReplyJson(status, branch=brn, pid=pid, patch=p_json))


    @staticmethod
    @api.route('/upload/<string:brn>/<string:pid>', methods=['POST', 'GET'])
    def upload_file(brn, pid):
        '''
        <>/upload/v5/P00001
        '''
        br_store = file_folder(brn, pid)
        status = ErrorCode.ERR_SUCCESS

        if request.method == 'POST':
            PatchMaker.log.info("%s upload file to: brn=%s, pid=%s", request.remote_addr, brn, pid)
            up_file = request.files['file']

            if not up_file:
                result = FileFormater(name='', type='', size=0, not_allowed_msg="invalid file")
                status = ErrorCode.ERR_INVALID_FILE
            else:
                mimetype = up_file.content_type
                filename = secure_filename(up_file.filename)
                PatchMaker.log.info('%s upload file %s', request.remote_addr, filename)
                if not allowed_file(up_file.filename):
                    result = FileFormater(name=filename, type=mimetype, not_allowed_msg="file type not allowed")
                    status = ErrorCode.ERR_DENIED_FILE
                else:
                    uploaded_file_path = os.path.join(br_store, filename)
                    up_file.save(uploaded_file_path)
                    size = os.path.getsize(uploaded_file_path)
                    result = FileFormater(name=filename, type=mimetype, size=size, brn=brn, pid=pid)
            return jsonify(ReplyJson(status, branch=brn, pid=pid, files=[result.get_file()]))
        else:
            PatchMaker.log.info('from upload retrieve file list : brn=%s, pid=%s', brn, pid)
            file_display = []
            if os.path.exists(br_store):
                files = [f for f in os.listdir(br_store) if os.path.isfile(os.path.join(br_store, f)) and f not in IGNORED_FILES]
                for f in files:
                    size = os.path.getsize(os.path.join(br_store, f))
                    file_saved = FileFormater(name=f, size=size, brn=brn, pid=pid)
                    file_display.append(file_saved.get_file())
            return jsonify(ReplyJson(status, branch=brn, pid=pid, files=file_display))


    @staticmethod
    @api.route('/download/<string:brn>/<string:pid>', methods=['GET'])
    @api.route('/download/<string:brn>/<string:pid>/<string:filename>', methods=['GET'])
    def download_files(brn, pid, filename=None):
        '''
        <>/download/v5/P00001?type=0           <= download patch file
        <>/download/v5/P00001?type=1           <= check patch file or not
        <>/download/v5/P00001?type=2           <= get source file list
        <>/download/v5/P00001/file1?type=0     <= download file1
        <>/download/v5/P00001/file1?type=1     <= check file1 exist or not
        
        id = 0:    <= download file
        id = 1:    <= check file exist
        id = 2:    <= get source file list
        '''
        type_id = int(request.values.get('type', 0))
        base_path = file_folder(brn, pid, filename is None)
        filename = pid.upper() + '.zip' if filename is None else filename

        status = ErrorCode.ERR_SUCCESS
        PatchMaker.log.info('brn=%s, pid=%s, filename=%s, type=%u', brn, pid, filename, type_id)

        if type_id == 0:
            # download patch file
            PatchMaker.log.info('download file = %s : %s', base_path, filename)
            if os.path.isfile(os.path.join(base_path, filename)):
                return send_from_directory(base_path, filename=filename, as_attachment=True, attachment_filename=filename)
        elif type_id == 1:
            # check if file exist
            PatchMaker.log.info('check file = %s : %s', base_path, filename)
            if os.path.isfile(os.path.join(base_path, filename)):
                return jsonify(ReplyJson(status, branch=brn, pid=pid, type=type_id, name=filename))
        elif type_id == 2:
            # get source file list
            PatchMaker.log.info('retrieve file list : brn=%s, pid=%s', brn, pid)
            file_display = []
            base_path = file_folder(brn, pid, False)
            for f in [f for f in os.listdir(base_path) if os.path.isfile(os.path.join(base_path, f)) and f not in IGNORED_FILES]:
                size = os.path.getsize(os.path.join(br_store, f))
                file_saved = FileFormater(name=f, size=size, brn=brn, pid=pid)
                file_display.append(file_saved.get_file())
            return jsonify(ReplyJson(status, branch=brn, pid=pid, type=type_id, files=file_display))
        
        PatchMaker.log.warn("no such file : filename: %s", filename)
        status = ErrorCode.ERR_NO_SUCH_FILE
        return jsonify(ReplyJson(status, branch=brn, pid=pid, type=type_id, name=filename))


    @staticmethod
    @api.route('/delete/<string:brn>/<string:pid>/<string:filename>', methods=['DELETE'])
    def delete_file(brn, pid, filename):
        '''
        <>/delete/v5/p00001/file1
        '''
        PatchMaker.log.info('%s delete file: brn=%s, pid=%s, filename=%s', request.remote_addr, brn, pid, filename)
        file_path = os.path.join(file_folder(brn, pid), filename)
        status = ErrorCode.ERR_SUCCESS

        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                PatchMaker.log.info('exception : %s', e)
                status = ErrorCode.ERR_DELETE_FILE
        else:
            status = ErrorCode.ERR_NO_SUCH_FILE
        return jsonify(ReplyJson(status, branch=brn, pid=pid, file=filename))