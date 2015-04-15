#!/usr/bin/env python

############################################################################
# Copyright (c) 2011-2013 Saint-Petersburg Academic University
# All Rights Reserved
# See file LICENSE for details.
############################################################################


import sys
import getopt
import os
import logging
import shutil

import ig_tools_init
import drawing_utils
import files_utils

def CheckBinaries(log):
    if not os.path.exists(ig_tools_init.PathToBins.paired_read_merger_tool):
        log.info("ERROR: Paired Read Merger tool was not found")
        sys.exit(1)

    if not os.path.exists(ig_tools_init.PathToBins.simulate_repertoire_tool):
        log.info("ERROR: Repertoire Simulator tool was not found")
        sys.exit(1)

    if not os.path.exists(ig_tools_init.PathToBins.create_ideal_repertoire_tool):
        log.info("ERROR: Ideal Repertoire Constructor tool was not found")
        sys.exit(1)

    if not os.path.exists(ig_tools_init.PathToBins.art_illumina):
        log.info("ERROR: ART Illumina read simulator was not found")
        sys.exit(1)

    if not os.path.exists(ig_tools_init.PathToBins.art_454):
        log.info("ERROR: ART 454 read simulator was not found")
        sys.exit(1)

class BaseOptions:
    long_options = "test skip-drawing".split()
    short_options = "o:"

class RepertoireSimulatorOptions:
    short_options = ""
    long_options = "num-bases= num-mutated= repertoire-size= chain-type= vgenes= dgenes= jgenes= tech= help".split()

class PairedReadMerger:
    long_options = "min-overlap= max-mismatch=".split()
    short_options = ""

class Options:
    output_dir = ""
    num_bases = 0
    num_mutated = 0
    repertoire_size = 0
    num_reads = 0

    chain_type = ""
    vgenes_path = ""
    dgenes_path = ""
    jgenes_path = ""

    repertoire_fasta = ""

    base_stats = ""
    mutated_stats = ""
    mutated_pos_stats = ""
    repertoire_stats = "" 

    technology = 'Illumina'
    left_reads = ""
    right_reads = ""

    min_overlap = 60
    max_mismatch = 0.1
    sim_mode = False

    merged_reads = ""
    ideal_repertoire_fa = ""
    ideal_repertoire_rcm = ""   
    
    draw_hist = True

    log = ""

def PrintOptions(options, log):
    log.info("\nInput parameters:")
    log.info("Output dir:\t\t\t\t\t" + options.output_dir)
    log.info("Number of base sequences:\t\t\t" + str(options.num_bases))
    log.info("Number of mutated sequences:\t\t\t" + str(options.num_mutated))
    log.info("Expected repertoire size:\t\t\t" + str(options.repertoire_size))
    log.info("Expected number of reads:\t\t\t" + str(options.num_reads))
    log.info("Min allowed overlap size:\t\t\t" + str(options.min_overlap))
    log.info("Max allowed mismatch rate:\t\t\t" + str(options.max_mismatch))
    log.info("Simulated technology:\t\t\t\t" + str(options.technology))

def usage(log):
    log.info("./ig_repertoire_simulator.py [options] --chain-type TYPE --num-bases N1 --num-mutated N2 --repertoire-size N3 -o <output-dir>")
    log.info("\nBasic options:")
    log.info("  -o\t\t\t<output_dir>\t\t\tdirectory to store all the resulting files (required)")
    log.info("  --chain-type\t\tHC/LC\t\tchain type: HC - heavy chain or LC - light chain (required)")
    log.info("  --num-bases\t\t<int>\t\t\t\tnumber of base sequences for simulation of reference repertoire (required)")
    log.info("  --num-mutated\t\t<int>\t\t\t\texpected number of mutated sequences for simulation of reference repertoire (required)")
    log.info("  --repertoire-size\t<int>\t\t\t\texpected size of simulated repertoire (required)")
    log.info("  --HC-LC\t\t<int-int>\t\t\tpercentage of heavy and light chain reads in final repertoire [default: '100-0']. Option is in developing")
    log.info("  --test\t\t\t\t\t\truns test dataset")

    log.info("\nAdvanced options:")
    log.info("  --HV\t\t\t<filename>\t\t\tFASTA file with Ig germline HV genes")
    log.info("  \t\t\t\t\t\t\t[default: 'src/ig_tools/human_ig_germline_genes/human_IGHV.fa']")
    log.info("  --HD\t\t\t<filename>\t\t\tFASTA file with Ig germline HD genes")
    log.info("  \t\t\t\t\t\t\t[default: 'src/ig_tools/human_ig_germline_genes/human_IGHD.fa']")
    log.info("  --HJ\t\t\t<filename>\t\t\tFASTA file with Ig germline HJ genes")
    log.info("  \t\t\t\t\t\t\t[default: 'src/ig_tools/human_ig_germline_genes/human_IGHJ.fa']\n")

    #log.info("  --tech\t\t<illumina/454>\t\t\tNGS technology for read simulation")
    #log.info("  --min-overlap\t\t<int>\t\t\t\tminimal allowed size of overlap in paired reads merging [default: '60']")
    #log.info("  --max-mismatch\t<float>\t\t\t\tmaximal allowed mismatch of overlap in paired reads merging [default: '0.1']")
    log.info("  --skip-drawing\t\t\t\t\tskips visualization of statistics for merged reads")
    log.info("  --help\t\t\t\t\t\tprints help")

def PrepareOutputDir(output_dir_path):
    if os.path.exists(output_dir_path):
        shutil.rmtree(output_dir_path)
    os.makedirs(output_dir_path)

# -------------------------- IgRepertoireSimulation --------------------------------------------

def CheckVDJgenes(options, self_dir_path, log):
    inner_vgenes = os.path.join(ig_tools_init.home_directory, "src/ig_tools/human_ig_germline_genes/human_IGHV.fa")
    inner_dgenes = os.path.join(ig_tools_init.home_directory, "src/ig_tools/human_ig_germline_genes/human_IGHD.fa")
    inner_jgenes = os.path.join(ig_tools_init.home_directory, "src/ig_tools/human_ig_germline_genes/human_IGHJ.fa")
    if not os.path.exists(options.vgenes_path):
        if not os.path.exists(os.path.abspath(inner_vgenes)):
            log.info("ERROR: FASTA file with HV genes was not found")
            sys.exit(1)
        options.vgenes_path = os.path.join(self_dir_path, inner_vgenes)
        log.info("FASTA file with V genes was not specified. IMGT database " + options.vgenes_path + " will be used by default")

    if not os.path.exists(options.dgenes_path):
        if not os.path.exists(os.path.abspath(inner_dgenes)):
            log.info("ERROR: FASTA file with HD genes was not found")
            sys.exit(1)
        options.dgenes_path = os.path.join(self_dir_path, inner_dgenes)
        log.info("FASTA file with D genes was not specified. IMGT database " + options.dgenes_path + " will be used by default")

    if not os.path.exists(options.jgenes_path):
        if not os.path.exists(os.path.abspath(inner_jgenes)):
            log.info("ERROR: FASTA file with HJ genes was not found")
            sys.exit(1)
        options.jgenes_path = os.path.join(self_dir_path, inner_jgenes)
        log.info("FASTA file with J genes was not specified. IMGT database " + options.jgenes_path + " will be used by default")

def CheckForRepertoireSimulationResults(options, log):
    options.repertoire_fasta = os.path.join(options.output_dir, "repertoire.fasta")
    if os.path.exists(options.repertoire_fasta):
        log.info("* Simulated reperoire was written to "+ options.repertoire_fasta)
    else:
        log.info("ERROR: FASTA file with simulated repetoire was not found")
        sys.exit(1)

    options.base_stats = os.path.join(options.output_dir, "base_repertoire.stats")
    if os.path.exists(options.base_stats):
        log.info("* Statistics for base sequences were written to " + options.base_stats)
    else:
        log.info("ERROR: File with statistics for base sequences was not found")
        sys.exit(1)
        
    options.mutated_stats = os.path.join(options.output_dir, "mutated_repertoire.stats")
    if os.path.exists(options.mutated_stats):
        log.info("* Statistics for mutated sequences were written to " + options.mutated_stats)
    else:
        log.info("ERROR: File with statistics for mutated sequences was not found")
        sys.exit(1)
        
    options.mutated_pos_stats = os.path.join(options.output_dir, "mutation_positions.stats")
    if os.path.exists(options.mutated_pos_stats):
        log.info("* Statistics for mutation positions were written to " + options.mutated_pos_stats)
    else:
        log.info("ERROR: File with statistics for mutation positions was not found")    
        sys.exit(1)

    options.repertoire_stats = os.path.join(options.output_dir, "final_repertoire.stats")
    if os.path.exists(options.repertoire_stats):
        log.info("* Statistics for final repertoire were written to " + options.repertoire_stats)
    else:
        log.info("ERROR: File with statistics for final repertoire was not found")
        sys.exit(1)
        
def DrawBaseStats(options, base_lens, base_freqs, log):
    hist_name1 = os.path.join(options.output_dir, "base_seq_lens.png")
    len_hist_settings = drawing_utils.GetGraphicalSettings(xlabel = "Sequence length", ylabel = "Sequence number", output_filename = hist_name1)
    drawing_utils.DrawHistogram(base_lens, len_hist_settings)
    if os.path.exists(hist_name1):
        log.info("* Histogram of distribution of base sequence lengths was written to " + hist_name1)
    else:
        log.info("ERROR: Histogram of distribution of base sequence lengths was not found")
        sys.exit(1)
    
    hist_name2 = os.path.join(options.output_dir, "base_seq_freq.png")
    freq_hist_settings = drawing_utils.GetGraphicalSettings(xlabel = "Sequence frequency", ylabel = "Sequence number", output_filename = hist_name2)
    drawing_utils.DrawHistogram(base_freqs, freq_hist_settings)
    if os.path.exists(hist_name2):
        log.info("* Histogram of distribution of base sequence frequencies was written to " + hist_name2)
    else:
        log.info("ERROR: Histogram of distribution of base sequence frequencies was not found")
        sys.exit(1)

def DrawMutatedStats(options, mutated_freqs, mutation_pos, log):
    hist_name1 = os.path.join(options.output_dir, "mutated_seq_freq.png")
    freq_hist_settings = drawing_utils.GetGraphicalSettings(xlabel = "Sequence frequency", ylabel = "Sequence number", output_filename = hist_name1)
    drawing_utils.DrawHistogram(mutated_freqs, freq_hist_settings)
    if os.path.exists(hist_name1):
        log.info("* Histogram of distribution of mutated sequences frequencies was written to " + hist_name1)
    else:
        log.info("ERROR: Histogram of distribution of mutated sequences frequencies was not found")
        sys.exit(1)

    hist_name2 = os.path.join(options.output_dir, "mutation_positions.png")
    pos_hist_settings = drawing_utils.GetGraphicalSettings(xlabel = "Relative mutation position", ylabel = "Mutation number", output_filename = hist_name2)
    drawing_utils.DrawHistogram(mutation_pos, pos_hist_settings)
    if os.path.exists(hist_name2):
        log.info("* Histogram of somatic mutation positions was written to " + hist_name2)
    else:
        log.info("ERROR: Histogram of somatic mutation positions was not found")
        sys.exit(1)

def PrepareMutationPositions(mutation_position, seq_len):
    rel_mutation_pos = list()
    for i in range(0, len(mutation_position)):
        rel_mutation_pos.append(mutation_position[i] / seq_len[i])
    return rel_mutation_pos

def VisualizeRepertoireStats(options, log) :
    if not options.draw_hist:
        return 

    log.info("\n==== Visualization of repertoire statistics")

    base_data = files_utils.ReadData(options.base_stats)
    DrawBaseStats(options, files_utils.StrListToInt(base_data.data["col2"]), files_utils.StrListToInt(base_data.data["col3"]), log)

    mutated_data = files_utils.ReadData(options.repertoire_stats)
    mutated_freq = files_utils.StrListToInt(mutated_data.data["col2"])
    mutation_pos_data = files_utils.ReadData(options.mutated_pos_stats)
    mutation_pos_list = PrepareMutationPositions(files_utils.StrListToFloat(mutation_pos_data.data["col1"]), files_utils.StrListToFloat(mutation_pos_data.data["col2"]))
    DrawMutatedStats(options, mutated_freq, mutation_pos_list, log)

def GetSimulatorCommandLine(options, path_to_binary):
    command_line = path_to_binary + " " + options.chain_type + " " + options.output_dir + " " + str(options.num_bases) + " " + str(options.num_mutated) + " " + str(options.repertoire_size) + " " + options.vgenes_path + " "
    if options.chain_type == "HC":
        return command_line + options.dgenes_path + " " + options.jgenes_path
    return command_line + options.jgenes_path

def RunRepertoireSimulation(options, path_to_binary, self_dir_path, log):
    CheckVDJgenes(options, self_dir_path, log)
    command_line = GetSimulatorCommandLine(options, path_to_binary)
    log.info("Repertoire simulator command line: " + command_line)
    log.info('\n==== Reference repertoire simulation')
    error_code = os.system(command_line + " 2>&1 | tee -a " + options.log)

    if error_code != 0:
        AbnormalFinishMsg(log, "repertoire_simulator")
        sys.exit(1)

    CheckForRepertoireSimulationResults(options, log)
    VisualizeRepertoireStats(options, log)

# -------------------------- Read Simulator --------------------------------------------

def RunReadSimulator(options, log):
    log.info('\n==== Read Simulator (ART) starts')

    command_line = ""
    if options.technology == "Illumina":
        command_line = ig_tools_init.PathToBins.run_art_illumina
        command_line = command_line + " -i " + options.repertoire_fasta + " -p -l 250 -f 1 -m 350 -s 50 -o " + os.path.join(options.output_dir, "paired_reads")
    if options.technology == "454":
        command_line = ig_tools_init.PathToBins.run_art_454
        command_line = command_line + " " + options.repertoire_fasta + " " + os.path.join(options.output_dir, "paired_reads") + " 1 350 50"
    log.info("ART's command line: " + command_line)
    error_code = os.system(command_line + " 2>&1 | tee -a " + options.log) 

    if error_code != 0:
        AbnormalFinishMsg(log, "ART")
        sys.exit(1)

    options.left_reads = os.path.join(options.output_dir, "paired_reads1.fq")
    options.right_reads = os.path.join(options.output_dir, "paired_reads2.fq")

    if not os.path.exists(options.left_reads) or not os.path.exists(options.right_reads):
        log.info("ERROR: Simulated paired-end reads were not found")
        sys.exit(1)

    log.info("* Simulated paired-end reads were written to " + options.left_reads + " and " + options.right_reads)

# -------------------------- Splitting paired reads --------------------------------------------

#def RunSplittingPairedFastq(options, path_to_binary, log):
    # log.info('\n==== Splitting paired reads')
    # command_line = path_to_binary + " " + options.paired_unsplitted_reads + " " + options.dataset_name
    # error_code = os.system(command_line + " 2>&1 | tee -a " + options.log)
    #
    # if error_code != 0:
    #     AbnormalFinishMsg(log, "paired_reads_splitter")
    #     sys.exit(1)
    #
    # options.left_reads = options.dataset_name + "left_reads.fastq"
    # if os.path.exists(options.left_reads):
    #     log.info("* Left reads were written to " + options.left_reads)
    # else:
    #     log.info("ERROR: FASTQ with left reads after splitting was not found")
    #     sys.exit(1)
    #
    # options.right_reads = options.dataset_name + "right_reads.fastq"
    # if os.path.exists(options.right_reads):
    #     log.info("* Right reads were written to " + options.right_reads)
    # else:
    #     log.info("ERROR: FASTQ with right reads after splitting was not found")
    #     sys.exit(1)

# -------------------------- PairedReadMerger --------------------------------------------

def RunPairedReadMerger(options, path_to_binary, log):
    log.info('\n==== Paired reads merging')
    command_line = path_to_binary + " " + options.left_reads + " " + options.right_reads + " " + os.path.join(options.output_dir, "merged_reads") + " --min-overlap=" + str(options.min_overlap) + " --max-mismatch=" + str(options.max_mismatch)
    #if options.sim_mode:
    #    command_line = command_line + " --simulated-mode"
    error_code = os.system(command_line + " 2>&1 | tee -a " + options.log)

    if error_code != 0:
        AbnormalFinishMsg(log, "paired_read_merged")
        sys.exit(1)

    options.merged_reads = os.path.join(options.output_dir, "merged_reads.fastq")
    if os.path.exists(options.merged_reads):
        log.info("* Merged reads were written to " + options.merged_reads)
    else:
        log.info("ERROR: FASTQ file with merged reads was not found")
        sys.exit(1)

# -------------------------- IdealRepertoireConstruction -----------------------------------

def RunIdealRepertoireConstruction(options, path_to_binary, log):
    log.info("\n==== Ideal repertoire construction")
    command_line = path_to_binary + " " + options.merged_reads + " " + os.path.join(options.output_dir, "ideal_repertoire")
    error_code = os.system(command_line + " 2>&1 | tee -a " + options.log)

    if error_code != 0:
        AbnormalFinishMsg(log, "ideal_repertoire_constructor")
        sys.exit(1)
    
    options.ideal_repertoire_fa = os.path.join(options.output_dir, "ideal_repertoire.clusters.fa")
    options.ideal_repertoire_rcm = os.path.join(options.output_dir, "ideal_repertoire.rcm")
    if os.path.exists(options.ideal_repertoire_fa) and os.path.exists(options.ideal_repertoire_rcm):
        log.info("Ideal repertoire was successfully created:")
        log.info("* CLUSTERS.FASTA for simulated repertoire was written to " + options.ideal_repertoire_fa)
        log.info("* RCM for simulated repertoire was written to " + options.ideal_repertoire_rcm)
    else:
        log.info("ERROR: CLUSTERS.FASTA and RCM for simulated repertoire were not found")
        sys.exit(1)

#--------------------------- Cleanup --------------------------------------------

#def Cleanup(options):
# nothing to do :)

# -------------------------- ParseInputParams -----------------------------------
def DetermineErrorType(options, arg):
    if arg in options.error_type_set:
        options.error_type = options.error_type_set[arg]
    else:
        options.error_type = options.error_type_set['linear']
    if options.error_type == options.error_type_set['linear']:
        options.sim_mode = False
    else:
        options.sim_mode = True

def CheckOptionsCorrectness(options, log):
    if options.chain_type != 'HC' and options.chain_type != 'LC':
        log.info("ERROR: Incorrect type of chain (--chain-type) should be equal HC or LC")
        usage.log()
        sys.exit(1) 
    if options.num_bases == 0:
        log.info("ERROR: Number of base sequences (--num-bases) is a mandatory parameter!")
        usage(log)
        sys.exit(1)
    if options.num_mutated == 0:
        log.info("ERROR: Number of mutated sequences (--num-mutated) is a mandatory parameter!")
        usage(log)
        sys.exit(1)
    if options.repertoire_size == 0:
        log.info("ERROR: Expected repertoire size (--repertoire-size) is a mandatory parameter!")
        usage(log)
        sys.exit(1)
    if options.num_bases >= options.num_mutated:
        log.info("ERROR: Number of mutated sequences (--num-mutated) should be greater than number of base sequences (--num-bases)")
        usage(log)
        sys.exit(1)
    if options.num_mutated >= options.repertoire_size:
        log.info("ERROR: Repertoire size (--repertoire-size) should be greater than number of mutated sequences (num-mutated)")
        usage(log)
        sys.exit(1)
    if options.max_mismatch < 0 or options.max_mismatch > 1:
        log.info("ERROR: Maximal allowed mismatch rate (--max-mismatch) should be from [0, 1]")
        usage(log)
        sys.exit(1)
    if options.technology != "illumina" and options.technology != "454":
        log.info("ERROR: Option value " + options.technology + " was not recognized. Technology for NGS read simulation should be \"illumina\" or \"454\"")

def PrintMainOutputFiles(options, log):
    log.info("\nMain output files:")
    log.info("* Sequences of simulated repertoire were written to " + options.repertoire_fasta) 
    log.info("* Simulated merged reads were written to " + options.merged_reads)
    log.info("* CLUSTERS.FA for simulated repertoire were written to " + options.ideal_repertoire_fa)
    log.info("* RCM for simulated repertoire were written to " + options.ideal_repertoire_rcm)

# -------------------------- main -----------------------------------

def ParseCommandLine(options, log):
    options_dict = Options()
    for opt, arg in options:
        if opt == '-o':
            options_dict.output_dir = arg + "/"
        elif opt == '--num-bases':
            options_dict.num_bases = int(arg)
        elif opt == '--num-mutated':
            options_dict.num_mutated = int(arg)
        elif opt == '--repertoire-size':
            options_dict.repertoire_size = int(arg)
            options_dict.num_reads = int(arg) * 2
        elif opt == '--chain-type':
            options_dict.chain_type = arg
        elif opt == '--vgenes':
            options_dict.vgenes_path = arg
        elif opt == '--dgenes':
            options_dict.dgenes_path = arg
        elif opt == '--jgenes':
            options_dict.jgenes_path = arg
        elif opt == '--min-overlap':
            options_dict.min_overlap = int(arg)
        elif opt == '--max-mismatch':
            options_dict.max_mismatch = float(arg)
        elif opt == "--tech":
            options_dict.technology = arg
        elif opt == '--test':
            options_dict.num_bases = 10
            options_dict.num_mutated = 50
            options_dict.repertoire_size = 1000
            options_dict.output_dir = 'ig_simulator_test/'
        elif opt == '--skip-drawing':
            options_dict.draw_hist = False
        elif opt == '--help':
            usage(log)
            sys.exit(0)
    return options_dict

def RunIgSimulator(options_dict, log):
    log.info("\n======== IgSimulator starts")
    # run repertoire simulator
    RunRepertoireSimulation(options_dict, ig_tools_init.PathToBins.run_simulate_repertoire_tool, ig_tools_init.home_directory, log)
    # run read simulator
    RunReadSimulator(options_dict, log)
    # splitting paired reads
    #RunSplittingPairedFastq(options_dict, ig_tools_init.PathToBins.run_split_paired_fastq_reads_tool, log)
    # merging splitted reads
    RunPairedReadMerger(options_dict, ig_tools_init.PathToBins.run_paired_read_merger_tool, log)
    # ideal repertoire construction
    RunIdealRepertoireConstruction(options_dict, ig_tools_init.PathToBins.run_create_ideal_repertoire_tool, log)
    # cleanup
    #Cleanup(options_dict)
    log.info("\n======== IgSimulator ends")
    PrintMainOutputFiles(options_dict, log)

def main():
    # prepare log
    log = logging.getLogger('ig_simulator')
    log.setLevel(logging.DEBUG)
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter('%(message)s'))
    console.setLevel(logging.DEBUG)
    log.addHandler(console)

    CheckBinaries(log)

    # all options
    all_long_options = list(set(BaseOptions.long_options + RepertoireSimulatorOptions.long_options))
    all_short_options = BaseOptions.short_options + RepertoireSimulatorOptions.short_options

    # preparing command line arguments
    try:
        options, not_options = getopt.gnu_getopt(sys.argv, all_short_options, all_long_options)
    except getopt.GetoptError:
        _, exc, _ = sys.exc_info()
        sys.stderr.write(str(exc) + "\n")
        usage(log)
        sys.stderr.flush()
        sys.exit(1)
    if not options:
        usage(log)
        sys.stderr.flush()
        sys.exit(1)

    # parsing input params
    options_dict = ParseCommandLine(options, log)
    CheckOptionsCorrectness(options_dict, log)

    # preparation of directory
    options_dict.output_dir = os.path.join(ig_tools_init.home_directory, options_dict.output_dir)
    PrepareOutputDir(options_dict.output_dir)

    # preparation log
    log_filename = os.path.join(options_dict.output_dir, "ig_simulator.log")
    if os.path.exists(log_filename):
        os.remove(log_filename)
    log_handler = logging.FileHandler(log_filename, mode='a')
    log.addHandler(log_handler)
    options_dict.log = log_filename
    log.info("Log will be written to " + log_filename + "\n")

    # printing input params
    ig_tools_init.PrintCommandLine(sys.argv, log)
    PrintOptions(options_dict, log)

    # run of simulator
    try:
        RunIgSimulator(options_dict, log)
        log.info("\nThank you for using IgSimulator!")
    except (KeyboardInterrupt):
        log.info("\nIgSimulator was interrupted!")  
    except BaseException:
        exc_type, exc_value, _ = sys.exc_info()
        if exc_type == SystemExit:
            sys.exit(exc_value)
        else:
            log.exception(exc_value)
            log.info("\nERROR: Exception caught. Please contact us and send .log file")

    log.info("\nLog was written to " + log_filename)


if __name__ == '__main__':
    main()
