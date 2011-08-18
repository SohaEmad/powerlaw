def avalanche_analysis(data,bin_width=1, percentile=.99, event_method='amplitude', data_amplitude=0, method='grid'):
    """docstring for avalanche_analysis  """
    metrics = {}
    metrics['bin_width'] = bin_width
    metrics['percentile'] = percentile
    metrics['event_method'] = event_method

    m = find_events(data, percentile, event_method, data_amplitude)
    metrics.update(m)

    from numpy import concatenate, array
    starts, stops = find_cascades(metrics['event_times'], bin_width, method)

    metrics['starts'] = starts
    metrics['stops'] = stops
    metrics['durations'] = stops-starts
    metrics['durations_silences'] = starts[1:]-stops[:-1]

    #For every avalanche, calculate some list of metrics, then save those metrics in a dictionary
    for i in range(len(starts)):
        m = avalanche_metrics(metrics, i)
        for k,v in m:
            metrics[k] = concatenate((metrics.setdefault(k,array([])), \
                    v))
    return metrics

def find_events(data_displacement, percentile=.99, event_method='amplitude', data_amplitude=0):
    """find_events does things"""
    from scipy.signal import hilbert
    from scipy.stats import scoreatpercentile
    from numpy import ndarray, transpose, where, diff, sort
    
    n_rows, n_columns = data_displacement.shape
    data_displacement = data_displacement-data_displacement.mean(1).reshape(n_rows,1)

    if type(data_amplitude)!=ndarray:
        data_amplitude = abs(hilbert(data_displacement))

    if event_method == 'amplitude':
        signal = data_amplitude
    elif event_method == 'displacement':
        signal = abs(data_displacement)
    elif event_method == 'displacement_up':
        signal = data_displacement
    elif event_method == 'displacement_down':
        signal = data_displacement*-1.0
    else:
        print 'Please select a supported event detection method (amplitude or displacement)'

    #scoreatpercentile only computes along the first dimension, so we transpose the 
    #(channels, times) matrix to a (times, channels) matrix. This is also useful for
    #applying the threshold, which is #channels long. We just need to make sure to 
    #invert back the coordinate system when we assign the results, which we do 
    threshold = scoreatpercentile(transpose(signal), percentile*100)
    times, channels = where(transpose(signal)>threshold)

    displacements = data_displacement[channels, times]
    amplitudes = data_amplitude[channels,times]
    interevent_intervals = diff(sort(times))

    data_amplitude_aucs = area_under_the_curve(data_amplitude)
    event_amplitude_aucs = data_amplitude_aucs[channels, times]
    data_displacement_aucs = area_under_the_curve(data_displacement)
    event_displacement_aucs = data_displacement_aucs[channels, times]

    output_metrics = { \
            'event_times': times, \
            'event_channels': channels,\
            'event_displacements': displacements,\
            'event_amplitudes': amplitudes,\
            'event_amplitude_aucs': event_amplitude_aucs,\
            'event_displacement_aucs': event_displacement_aucs,\
            'interevent_intervals': interevent_intervals,\
            }
    return output_metrics

def find_cascades(event_times, bin_width=1, method='grid'):
    """find_events does things"""
    from numpy import array, where, diff, concatenate

    if method=='gap':
        starts = array([event_times[0]])
        stops = array([event_times[-1]])
        changes = where(diff(event_times)>=bin_width+1)[0]
        starts = concatenate((starts, event_times[changes+1]))
        stops = concatenate((event_times[changes], stops))

    elif method=='grid':
        from numpy import reshape, zeros, size, unique
        
        #Collapse the reaster into a vector of zeros and ones, indicating activity or inactivity on all channels
        raster = zeros(event_times.max()+1)
        raster[unique(event_times)] = 1
        
        #Find how short we'll be trying to fill the last bin, then pad the end
        data_points = raster.shape[0]
        short = bin_width - (data_points % bin_width)
        raster = concatenate((raster, zeros(short)), 1)
        
        #Reshaped the raster vector into a bin_width*bins array, so that we can easily collapse bins together without using for loops
        raster = reshape( raster, (raster.shape[0]/bin_width, bin_width) )
        
        #Collapse bins together and find where the system switches states
        raster = raster.sum(1)
        raster = raster>0
        raster = diff(concatenate((zeros((1)), raster, zeros((1))), 1))
        #raster = squeeze(raster)
        
        starts = (raster==1).nonzero()[0]
        stops = (raster==-1).nonzero()[0]
        
        #Expand the bin indices back into the indices of the original raster
        starts = starts*bin_width
        stops = stops*bin_width
        #Additionally, if the data stops midway through a bin, and there is an avalanche in that bin, the above code will put the stop index in a later,
        #non-existent bin. Here we put the avalanche end at the end of the recording
        if size(stops)>0 and stops[-1]>data_points:
            stops[-1] = data_points

    else:
        print 'Please select a supported cascade detection method (grid or gap)'

    return (starts, stops)

def avalanche_metrics(input_metrics, avalanche_number):
    """avalanche_metrics calculates various things"""
    from numpy import array, where
    avalanche_stop = where(input_metrics['event_times'] < \
            input_metrics['stops'][avalanche_number])[0][-1]+1
    avalanche_start = where(input_metrics['event_times'] >= \
            input_metrics['starts'][avalanche_number])[0][0]

#Calculate sizes
    size_events = array([avalanche_stop-avalanche_start])
    size_displacements = array([\
            sum(abs(\
            input_metrics['event_displacements'][avalanche_start:avalanche_stop]))\
            ])
    size_amplitudes = array([\
            sum(abs(\
            input_metrics['event_amplitudes'][avalanche_start:avalanche_stop]))\
            ])
    size_aucs = array([\
            sum(abs(\
            input_metrics['event_amplitude_aucs'][avalanche_start:avalanche_stop]))\
            ])
#Calculate sigmas
    if input_metrics['durations'][avalanche_number] < \
            (2*input_metrics['bin_width']):
                sigma_amplitudes = sigma_events = \
                        sigma_displacements = sigma_amplitude_aucs = \
                        array([0])
    else:
        first_bin = where( \
                input_metrics['event_times'] < \
                (input_metrics['starts'][avalanche_number] \
                +input_metrics['bin_width'])\
                )[0][-1]
        second_bin = where( \
                input_metrics['event_times'] < \
                (input_metrics['starts'][avalanche_number] \
                +2*input_metrics['bin_width'])\
                )[0][-1]+1
        
        sigma_events = array([\
                (second_bin-first_bin)/ \
                (first_bin-avalanche_start+1.0) \
                ])
        sigma_displacements = array([\
                sum(abs(input_metrics['event_displacements'][first_bin:second_bin]))/  \
                sum(abs(input_metrics['event_displacements'][avalanche_start:first_bin+1]))\
                ])
        sigma_amplitudes = array([\
                sum(abs(input_metrics['event_amplitudes'][first_bin:second_bin]))/  \
                sum(abs(input_metrics['event_amplitudes'][avalanche_start:first_bin+1]))\
                ])
        sigma_amplitude_aucs = array([\
                sum(abs(input_metrics['event_amplitude_aucs'][first_bin:second_bin]))/  \
                sum(abs(input_metrics['event_amplitude_aucs'][avalanche_start:first_bin+1]))\
                ])

#Calculate Tara's growth ratio
    event_times_within_avalanche = (\
            input_metrics['event_times'][avalanche_start:avalanche_stop] - \
            input_metrics['event_times'][avalanche_start]
            )
    #initial_events = where(event_times_within_avalanche==0)[0]

    from numpy import log2
    initial_amplitude = (\
            input_metrics['event_amplitudes'][avalanche_start].sum() \
            )
    t_ratio_amplitude = log2(\
            input_metrics['event_amplitudes'][avalanche_start:avalanche_stop] / \
            initial_amplitude \
            )

    initial_displacement = (\
            abs(input_metrics['event_displacements'][avalanche_start]).sum() \
            )
    t_ratio_displacement = log2(\
            abs(input_metrics['event_displacements'][avalanche_start:avalanche_stop]) / \
            initial_displacement \
            )

    initial_amplitude_auc = (\
            input_metrics['event_amplitude_aucs'][avalanche_start].sum() \
            )
    t_ratio_amplitude_auc = log2(\
            input_metrics['event_amplitude_aucs'][avalanche_start:avalanche_stop] / \
            initial_amplitude_auc \
            )

    initial_displacement_auc = (\
            abs(input_metrics['event_displacement_aucs'][avalanche_start]).sum() \
            )
    t_ratio_displacement_auc = log2(\
            abs(input_metrics['event_displacement_aucs'][avalanche_start:avalanche_stop]) / \
            initial_displacement_auc \
            )
    output_metrics = (\
            ('size_events', size_events), \
            ('size_displacements', size_displacements),\
            ('size_amplitudes', size_amplitudes),\
            ('size_aucs', size_aucs), \
            ('sigma_events', sigma_events), 
            ('sigma_displacements', sigma_displacements),\
            ('sigma_amplitudes', sigma_amplitudes),\
            ('sigma_amplitude_aucs', sigma_amplitude_aucs),\
            ('event_times_within_avalanche', event_times_within_avalanche), \
            ('t_ratio_amplitude', t_ratio_amplitude),\
            ('t_ratio_displacement', t_ratio_displacement),\
            ('t_ratio_amplitude_auc', t_ratio_amplitude_auc),
            ('t_ratio_displacement_auc', t_ratio_displacement_auc),
            )
    return output_metrics

def area_under_the_curve(data, baseline='mean'):
    """area_under_the_curve is currently a mentally messy but computationally fast way to get an array of area under the curve information, to be used to assign to events. The area under the curve is the integral of the deflection from baseline (mean signal) in which an event occurrs. area_under_the_curve returns an array of the same size as the input data, where the datapoints are the areas of the curves the datapoints are contained in. So, all values located within curve N are the area of curve N, all values located within curve N+1 are the area of curve N+1, etc. Note that many curves go below baseline, so negative areas can be returned."""
    from numpy import cumsum, concatenate, zeros, empty, shape, repeat, diff, where, sign, ndarray
    n_rows, n_columns = data.shape

    if baseline=='mean':
        baseline = data.mean(1).reshape(n_rows,1)
    elif type(baseline)!=ndarray:
        print 'Please select a supported baseline_method (Currently only support mean and an explicit array)'

    #Convert the signal to curves around baseline
    curves_around_baseline = data-baseline

    #Take the cumulative sum of the signals. This will be rising during up curves and decreasing during down curves
    sums = cumsum(curves_around_baseline, axis=-1)
    #Find where the curves are, then where they stop
    z = zeros((n_rows,1))
    sums_to_diff = concatenate((z, sums, z), axis=-1)
    curving = sign(diff(sums_to_diff)) #1 during up curve and -1 during down curve
    curve_changes = diff(curving) #-2 at end of up curve and 2 at end of down curve
    curve_changes[:,-1] = 2 # Sets the last time point to be the end of a curve
    stop_channels, stop_times =where(abs(curve_changes)==2)
    stop_times = stop_times.clip(0,n_columns-1) #corrects for a +1 offset that can occur in a curve that ends at the end of the recording (in order to detect it we add an empty column at the end of the time series, but that puts the "end" of the curve 1 step after the end of the time series)

    data_aucs = empty(shape(data))
    for i in range(n_rows):
    #The value in the cumulative sum at a curve's finish will be the sum of all curves so far. So the value of the most recently finished curve is just the cumsum at this curve minus the cumsum at the end of the previous curve
        curves_in_row = where(stop_channels==i)[0]
        stops_in_row = stop_times[curves_in_row]
        if stops_in_row[0]==1: #If the first stop occurs at index 1, that means there's a curve at index 0 of duration 1
            stops_in_row = concatenate(([0],stops_in_row))
        values = sums[i,stops_in_row]-concatenate(([0],sums[i,stops_in_row[:-1]]))
        previous_stops = concatenate(([-1], stops_in_row[:-1]))
        durations = stops_in_row-previous_stops
        data_aucs[i] = repeat(values, durations)

    return data_aucs