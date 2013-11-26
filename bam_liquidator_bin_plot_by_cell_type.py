#!/usr/bin/env python

##################################################################################
# The MIT License (MIT)
#
# Copyright (c) 2013 John DiMatteo 
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
##################################################################################

import bokeh.plotting as bp
import numpy as np
import MySQLdb

db = MySQLdb.connect(user="counter", db="meta_analysis")
version = "203"

def cell_types():
    # todo: memoize 
    types = ['be2c', 'dhl6', 'ec', 'hbl1', 'hsc', 'k422', 'kbm7', 'kms11', 'ly1', 'ly18', 'ly3', 'ly4', 'mm1s', 'mmp1', 'nut797', 'p107a', 'p14a', 'p265', 'p286', 'p397', 'p448', 'p493-6', 'sknas', 'toledo']
    if len(types) == 0:
        print "Getting cell types"
        cursor = db.cursor()
        cursor.execute("SELECT distinct cell_type FROM chr1_bin_counts_by_cell_type")

        for row in cursor.fetchall():
            types.append(row[0]) 

        print types        
    else:
        print "Using saved cell types from Mon Nov 18 08:38:40 EST 2013"
        
    return types 

def file_names(cell_type, common_clause):
    # todo: memoize 
    file_names = []
   
    if cell_type == 'be2c':
        file_names = ['01102013_D1L0CACXX_5.ACAGTG.hg18.bwt.sorted.bam', '01102013_D1L0CACXX_5.ACTTGA.hg18.bwt.sorted.bam', '01102013_D1L0CACXX_5.CAGATC.hg18.bwt.sorted.bam', '01102013_D1L0CACXX_5.GCCAAT.hg18.bwt.sorted.bam', '04052013_C21THACXX_3.AGTTCC.hg18.bwt.sorted.bam', '04052013_C21THACXX_3.CCGTCC.hg18.bwt.sorted.bam', '04052013_C21THACXX_3.GTCCGC.hg18.bwt.sorted.bam', '04052013_C21THACXX_3.GTGAAA.hg18.bwt.sorted.bam', 'L228_100_BE2C_CECR2.hg18.bwt.sorted.bam', 'L228_101_BE2C_H3K27ME3.hg18.bwt.sorted.bam'] 
        print "Using saved file names from Mon Nov 18 14:53:28 EST 2013"
    else:
        print "Getting file names for cell type " + cell_type
        cursor = db.cursor()
        cursor.execute("SELECT distinct file_name FROM counts where " + common_clause 
                       + " AND parent_directory = '" + cell_type + "' ")

        for row in cursor.fetchall():
            file_names.append(row[0]) 

        print cell_type + ": " + str(file_names) 
        
    return file_names 

def plot(chromosome, common_clause):
    bp.output_file(chromosome + ".html")

    print "Plotting summary"

    cursor = db.cursor()

    overall_sql = "SELECT bin, SUM(count_fraction) AS count FROM normalized_bins WHERE " + common_clause + " GROUP BY bin"

    cursor.execute(overall_sql)

    # todo: I should probably be able to do something like the following without copying: 
    #       bp.scatter(cursor.fetchall())

    bin_number = [] 
    count = [] 
    
    for row in cursor.fetchall():
        bin_number.append(int(row[0]))
        count.append(float(row[1]))

    overall = bp.scatter(bin_number, count)
    overall.title = "counts per bin across all bam files"

    for cell_type in cell_types():
        print "Plotting " + cell_type

        bin_number = [] 
        count = [] 
        
        cell_type_bin_sql = "SELECT bin, count_fraction FROM normalized_bins WHERE " + common_clause + "AND cell_type = '%s'" % cell_type  

        cell_type_cursor = db.cursor()
        cell_type_cursor.execute(cell_type_bin_sql)
        for cell_type_row in cell_type_cursor.fetchall():
            bin_number.append(int(cell_type_row[0]))
            count.append(float(cell_type_row[1]))

        cell_type_plot = bp.scatter(bin_number, count)
        cell_type_plot.title = "%s counts per bin" % cell_type 

    bp.save()
    #bp.show()

def total_count_for_file(file_name, common_clause):
    cursor = db.cursor()
    cursor.execute("SELECT SUM(count) FROM counts "
                    "WHERE " + common_clause + " AND file_name = '" + file_name + "' ")
    count = 0

    for row in cursor.fetchall():
        count = row[0]
        break

    return count
    

def populate_count_fractions(chromosome, common_clause):
    for cell_type in cell_types():
        print "Processing cell_type " + cell_type

        files = file_names(cell_type, common_clause)

        processed_a_single_file_for_this_cell_type = False

        for file_name in files: 
            print "Processing " + file_name 
            file_total_count = total_count_for_file(file_name, common_clause)

            bin_cursor = db.cursor()
            bin_cursor.execute("SELECT bin, count FROM counts WHERE " + common_clause
                               + " AND file_name = '" + file_name + "' ")

            divisor = float(file_total_count * len(files))

            for bin_row in bin_cursor.fetchall():
                bin_number = int(bin_row[0])
                bin_count = float(bin_row[1])

                if divisor != 0:
                    count_fraction = bin_count / divisor 
                else:
                    count_fraction = 0
                
                update_cursor = db.cursor()

                # todo: let mysql bind the variables instead of me building up custom sql strings
                if not processed_a_single_file_for_this_cell_type:
                    update_cursor.execute("INSERT INTO normalized_bins "
                                          "(cell_type, chromosome, bin, count_fraction, counter_version) "
                                          "VALUES ('%s', '%s', %d, %d, %s)" % (cell_type, chromosome, bin_number, 0, version) )

                update_cursor.execute("UPDATE normalized_bins SET count_fraction = count_fraction + %f "
                                       "WHERE counter_version = %s AND chromosome = '%s' AND cell_type = '%s' AND bin = %d "
                                       % (count_fraction, version, chromosome, cell_type, bin_number))

            processed_a_single_file_for_this_cell_type = True

def populate_count_percentiles(chromosome, common_clause):
    for cell_type in cell_types():
        print "Processing cell_type " + cell_type
        
        query_cursor = db.cursor()
        query_cursor.execute("SELECT bin, count_fraction FROM normalized_bins "
                              "WHERE " + common_clause + " AND cell_type = '" + cell_type + "' ORDER BY bin")

        array = np.zeros(query_cursor.rowcount)

        i=0
        for count_row in query_cursor.fetchall():
            bin_number = count_row[0]
            count_fraction = count_row[1]
            if i != bin_number:
                print "Error: unexpected missing bin: %d" % bin_number
                return

            array[i] = count_fraction
            i += 1

        percentiles = np.percentile(array, range(100)) 

        bin_number = 0
        for count_fraction in array:
            # find the highest percentile value < count_fraction
            percentile = 0
            for percentile_value in percentiles:
                if percentile_value >= count_fraction:
                    break

                percentile += 1
             
            update_cursor = db.cursor()

            # todo: this results in hottest bins being in the 100th percentile -- is that OK?
            update_cursor.execute("UPDATE normalized_bins SET percentile_in_cell_type = " + str(percentile) + " "
                                   "WHERE " + common_clause + " AND cell_type = '%s' AND bin = %d "
                                   % (cell_type, bin_number))

            bin_number += 1



if __name__ == "__main__":
    chromosomes = [ 'chr1', 'chr2', 'chr3', 'chr4', 'chr5', 'chr6', 'chr8', 'chr9', 'chrX', 'chr10', 'chr11', 'chr12', 'chr13', 'chr14', 'chr15', 'chr16', 'chr17', 'chr18', 'chr19', 'chr20', 'chr21', 'chr22' ]

    for chromosome in chromosomes:
        print "Processing " + chromosome
        common_clause = " counter_version = %s AND chromosome = '%s' " % (version, chromosome)

        populate_count_fractions(chromosome, common_clause)
        populate_count_percentiles(chromosome, common_clause)
        plot(chromosome, common_clause)

