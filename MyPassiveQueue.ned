//
// This file is part of an OMNeT++/OMNEST simulation example.
//
// Copyright (C) 2006-2015 OpenSim Ltd.
//
// This file is distributed WITHOUT ANY WARRANTY. See the file
// `license' for details on this and other legal matters.
//

import org.omnetpp.queueing.PassiveQueue;
//
// Passive queue. Messages have to be requested via direct method call.
// Its output must be connected to a Server.
//
// @author rhornig
// @todo minDelay not implemented
//
simple MyPassiveQueue
{
    parameters:
        @group(Queueing);
        @signal[dropped](type="long");
        @signal[queueLength](type="long");
        @signal[queueingTime](type="simtime_t");
        @statistic[dropped](title="drop event";record=vector?,count;interpolationmode=none);
        @statistic[queueLength](title="queue length";record=vector,timeavg,max;interpolationmode=sample-hold);
        @statistic[queueingTime](title="queueing time at dequeue";record=vector?,mean,max;unit=s;interpolationmode=none);
        @display("i=block/passiveq;q=queue");
        @signal[storeDeadline](type="simtime_t");
        @statistic[storeDeadline](title="deadline"; record=vector,stats; unit=s; interpolationmode=none);
		@signal[responseTime](type="simtime_t");
        @statistic[responseTime](title="Response Time"; record=vector,stats; unit=s; interpolationmode=none);
		//@signal[storeWifiTime](type="simtime_t");
       	//@statistic[storeWifiTime](title="Time in Wifi"; record=vector,stats; unit=s; interpolationmode=none);
		//@signal[storeCelTime](type="simtime_t");
        //@statistic[storeCelTime](title="Time in Cell"; record=vector,stats; unit=s; interpolationmode=none);

        int capacity = default(-1);  // negative capacity means unlimited queue
        bool fifo = default(true);   // whether the module works as a queue (fifo=true) or a stack (fifo=false)
        string sendingAlgorithm @enum("priority","random","roundRobin","minDelay") = default("priority");
                                     // how the queue tries to find a suitable server for an incoming job
    	volatile double switchToWi @unit(s);
        volatile double switchToCel @unit(s);
        volatile double deadline @unit(s);
     gates:
        input in[];
        output out[3];
}
