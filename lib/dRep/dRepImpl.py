# -*- coding: utf-8 -*-
#BEGIN_HEADER
import logging
import os
import sys
import shutil
import subprocess
import pprint
import uuid
import re
import functools
import pickle

from installed_clients.KBaseReportClient import KBaseReport
from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.WorkspaceClient import Workspace
from installed_clients.MetagenomeUtilsClient import MetagenomeUtils



from .util import PrintUtil, KBaseObjUtil, OutputUtil
from .util.PrintUtil import *


subprocess.run = functools.partial(subprocess.run, shell=True) 

#END_HEADER


class dRep:
    '''
    Module Name:
    dRep

    Module Description:
    A KBase module: dRep
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "0.0.1"
    GIT_URL = "https://github.com/n1mus/dRep.git"
    GIT_COMMIT_HASH = "05f421114e50a04008d9897cdb20399b23a47b46"

    #BEGIN_CLASS_HEADER
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.workspace_url = config['workspace-url']
        self.srv_wiz_url = config['srv-wiz-url']
        self.shared_folder = config['scratch']
        self.config = config
        self.config['callback_url'] = self.callback_url

        self.suffix = str(uuid.uuid4())

        self.ws = Workspace(self.workspace_url)
        self.mgu = MetagenomeUtils(self.callback_url)
        self.dfu = DataFileUtil(self.callback_url)
        self.dsu = KBaseObjUtil.DataStagingUtils(config)


        dprint('os.environ:', os.environ)
        dprint('config:', config)

        logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                            level=logging.INFO)
        #END_CONSTRUCTOR
        pass


    def dereplicate(self, ctx, params):
        """
        This example function accepts any number of parameters and returns results in a KBaseReport
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
 
        
        #BEGIN dereplicate

        dprint('ctx:', ctx)
        dprint('params:', params)


        dprint('ls -a /data/CHECKM_DATA', run='cli')
        dprint('cat /miniconda/lib/python3.6/site-packages/checkm/DATA_CONFIG', run='cli')




        # 
        ##
        ### input check: unique UPAs, unique names (in ui?)
        #### 
        #####
        ######

        '''
        if len(set(params['genomes_refs'])) < len(params['genomes_refs']):
            
            report = KBaseReport(self.callback_url)
            report_info = report.create({'report': {'objects_created':[],
                                                    'text_message': params['parameter_1']},
                                                    'workspace_name': params['workspace_name']})
            output = {
                'report_name': report_info['name'],
                'report_ref': report_info['ref'],
            }
        '''


        # 
        ##
        ### copy reference data into writeable area, set data root
        #### 
        #####
        ######

        dprint('ls -a /kb/module/data/CHECKM_DATA', run='cli')
        dprint('cat /miniconda/lib/python3.6/site-packages/checkm/DATA_CONFIG', run='cli')

        if params.get('workaround_refdata'):

            if not os.path.exists('/kb/module/data/CHECKM_DATA'):
                dprint('Copying reference tree into writeable location...')
                shutil.copytree('/data/CHECKM_DATA/', '/kb/module/data/CHECKM_DATA')

            subprocess.run('checkm data setRoot /kb/module/data/CHECKM_DATA', shell=True)


            dprint('ls -a /kb/module/data/CHECKM_DATA')
            dprint(subprocess.run('ls -a /kb/module/data/CHECKM_DATA', shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8'))

            dprint('cat /miniconda/lib/python3.6/site-packages/checkm/DATA_CONFIG')
            dprint(subprocess.run('cat /miniconda/lib/python3.6/site-packages/checkm/DATA_CONFIG', shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8'))





        #
        ##
        ### ds
        ####
        #####
        ######



        class BinnedContigs:
            '''
            DS for BinnedContigs information
            Very mutable
            '''

            loaded_instances = list()
            saved_instances = []
            
            dfu = self.dfu
            mgu = self.mgu
            dsu = self.dsu

            
            def __init__(self, upa, actions=['load'], **kwargs):
               
                self.loaded_instances.append(self)
                self.upa = upa

                for action in actions:
                    if 'load' == action: self.load()


            def load(self):
                ''''''
                mguObjData = self.mgu.binned_contigs_to_file(
                        {
                            'input_ref': binnedContigs_upa, 
                            'save_to_shock': 0
                        }
                ) # dict with just bin_file_directory

                self.bins_dir = mguObjData['bin_file_directory']
            
                dprint('os.listdir(bins_dir)', run=locals())

                wsObjData = self.ws.get_objects2(
                    {
                        'objects': [
                            {
                                'ref': binnedContigs_upa
                            }
                        ]
                    }
                ) # huge -- includes all the statistics


                self.name = wsObjData['data'][0]['info'][1]
                self.assembly_upa = binnedContigs_wsObjData['data'][0]['data']['assembly_ref']

                self.bin_name_list = []
                for bin_name in next(os.walk(bins_dir))[2]:
                    if not re.search(r'.*\.fasta$', bin_name):
                        dprint(f'WARNING: Found non .fasta bin name {bin_name} in dir {self.bins_dir} for BinnedContigs obj {self.name} with UPA {self.upa}', file=sys.stderr)
                    else:
                        self.bin_name_list.append(bin_name)
            
            
            def save(self, name, workspace_name):
                ''''''
                summary_path = self.dsu.build_bin_summary_file_from_binnedcontigs_obj(self.upa, self.bins_dir)
                dprint('summary_path', summary_path)

                mguFileToBinnedContigs_params = {
                    'file_directory': self.bins_dir,
                    'assembly_ref': self.assembly_upa,
                    'binned_contig_name': name,
                    'workspace_name': workspace_name
                }

                binnedContigs_objData = self.mgu.file_to_binned_contigs(mguFileToBinnedContigs_params)

                dprint('dRep_binnedContigs_objData', dRep_binnedContigs_objData)

                self.saved_instances.append(self)

                return {
                    'ref': dRep_binnedContigs_objData['binned_contig_obj_ref'],
                    'description': 'Dereplicated genomes for ' + binnedContigs_name
                }


            def pool(self, binsPooled_dir):
                '''for all bins, modify name and copy into binsPooled''' 
                for bin_name in self.bin_name_list:
                    bin_name_new = self.transform_binName(bin_name)         

                    bin_path = os.path.join(bins_dir, bin_name)
                    bin_path_new = os.path.join(binsPooled_dir, bin_name_new)

                    shutil.copyfile(bin_path, bin_path_new) 
                
            
            def transform_binName(self, bin_name):
                return self.upa.replace('/','-') + '__' + self.name + '__' + bin_name


            def reduce_to_dereplicated(self, bins_derep_dir):
                '''remove bins not in dereplicated'''
                bins_derep_name_list = os.listdir(bins_derep_dir)
                for bin_name in self.bin_name_list:
                    if self.transform_binName(bin_name) not in bins_derep_name_list:
                        os.remove(os.path.join(self.bins_dir, bin_name))









        # 
        ##
        ### Load input BinnedContigs files to scratch
        ####
        #####
        ######
       

        pkl_loc = '/kb/module/test/data/BinnedContigs_SURF-B_3bins_8bins.pkl'


        if params.get('skip_dl') and os.path.isfile(pkl_loc): # use test data
            with open(pkl_loc, 'rb') as f:
                BinnedContigs.loaded_instances = pickle.load(f)

        else:
            
            for binnedContigs_upa in params['genomes_refs']:
                BinnedContigs(binnedContigs_upa, actions=['load'])

            if not os.path.isfile(pkl_loc):
                with open(pickle_loc, 'wb') as f:
                    pickle.dump(BinnedContigs.loaded_instances, f)




        #
        ##
        ### pool
        ####
        #####
        ######
        
 
        binsPooled_dir = os.path.join(self.shared_folder, 'binsPooled_' + self.suffix)
        os.mkdir(binsPooled_dir)

        for binnedContigs in BinnedContigs.loaded_instances:
            binnedContigs.pool(binsPooled_dir)
        


        #
        ##
        ### Run dRep dereplicate -> gen workDir
        ####
        #####
        ######


        if params.get('skip_dRep'):
            dRep_workDir = '/kb/module/work/tmp/res.dRep.txwf.uniq'
            shutil.copytree('/kb/module/test/data/res.dRep.txwf.uniq', dRep_workDir)

        else:
            dRep_workDir = os.path.join(self.shared_folder, 'dRep_workDir_' + self.suffix)

            dRep_cmd = f'dRep dereplicate {dRep_workDir} -g {BinnedContigs.binsPooled_dir}/*.fasta --debug --checkM_method taxonomy_wf' 

            dprint(f'Running dRep cmd: {dRep_cmd}')
            dprint(dRep_cmd, run='cli')


        dprint('cat /miniconda/lib/python3.6/site-packages/checkm/DATA_CONFIG', run='cli')
        dprint('os.listdir(binsPooled_dir)', run=locals())
 



        #
        ##
        ### result BinnedContigs
        ####
        #####
        ######


        bins_derep_dir = os.path.join(dRep_workDir, 'dereplicated_genomes')
        objects_created = []


        # for each original BinnedContigs
        for binnedContigs in BinnedContigs.loaded_instances

            binnedContigs.reduce_to_dereplicated(bins_derep_dir)
            objects_created.append(binnedContigs.save(binnedContigs.name + ".dRep", params['workspace_name']))
            



        #
        ##
        ### HTML
        ####
        #####
        ######


        html_dir = os.path.join(self.shared_folder, 'html_dir_' + self.suffix)
        shutil.copytree('/kb/module/ui/output', html_dir) # dir of html and accessories

        
        html_path = os.path.join(html_dir, 'dRep_dereplicate_report.html')
        figures_dir = os.path.join(html_dir, 'figures')
        warnings_path = os.path.join(dRep_workDir, 'log/warnings.txt')
        
        htmlBuilder = OutputUtil.HTMLBuilder(html_path)

        # summary

        html_builder.build_summary(params['genomes_refs'], binnedContigs_naming_dict, transform_binName, dRep_workDir)

        # pdfs

        shutil.copytree(os.path.join(dRep_workDir, 'figures'), figures_dir)
        htmlBuilder.build_pdfs()

        # warnings

        with open(warnings_path) as f:
            warnings = f.read()
        htmlBuilder.build_warnings(warnings)


        # final build

        htmlBuilder.build()
       

        htmlZip_shockId = self.dfu.file_to_shock(
            {'file_path': html_dir, 
            'make_handle': 0,
            'pack': 'zip'})['shock_id']

        htmlZip_report_dict = {'shock_id': htmlZip_shockId,
                'name': 'dRep_dereplicate_report.html',
                'description': 'dRep dereplicate analyses and results' } 




        #
        ##
        ### return workDir
        ####
        #####
        ######

        


        dfuFileToShock_ret = self.dfu.file_to_shock({
            'file_path': dRep_workDir,
            'make_handle': 0,
            'pack': 'zip',
            })

        workDirZip_shockInfo = {
            'shock_id': dfuFileToShock_ret['shock_id'],
            'name': 'dRep_work_directory.zip',
            'description': 'Work directory used by dRep. Contains figures, (possibly) genome clustering warnings, logs, all intermediary files'
            }



        #
        ##
        ### Report
        ####
        #####
        ######


        #{
        #    'obj_name': dRep_binnedContigs_objName,
        #    'obj_ref': dRep_binnedContigs_objData['binned_contig_obj_ref']
        #}
       


        report_params = {'message': '',
                         'direct_html_link_index': 0,
                         'html_links': [htmlZip_report_dict],
                         'file_links': [workDirZip_shockInfo],
                         'report_object_name': 'dRep_report_' + self.suffix,
                         'workspace_name': params['workspace_name'],
                         'objects_created': objects_created
                         }

        kbr = KBaseReport(self.callback_url)
        report_output = kbr.create_extended_report(report_params)

        output = {
            'report_name': report_output['name'],
            'report_ref': report_output['ref'],
        }

        #END dereplicate

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method dereplicate return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]
    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]
