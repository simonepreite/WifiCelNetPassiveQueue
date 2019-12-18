//
// This file is part of an OMNeT++/OMNEST simulation example.
//
// Copyright (C) 2006-2015 OpenSim Ltd.
//
// This file is distributed WITHOUT ANY WARRANTY. See the file
// `license' for details on this and other legal matters.
//

#include "MyPassiveQueue.h"

#include "Job.h"
#include "MyServer.h"


Define_Module(MyPassiveQueue);

MyPassiveQueue::MyPassiveQueue()
{
    selectionStrategy = nullptr;
}

MyPassiveQueue::~MyPassiveQueue()
{
    delete selectionStrategy;
}

void MyPassiveQueue::initialize()
{
    droppedSignal = registerSignal("dropped");
    queueingTimeSignal = registerSignal("queueingTime");
    queueLengthSignal = registerSignal("queueLength");

    storeDeadline = registerSignal("storeDeadline");
    storeWifiTime = registerSignal("storeWifiTime");
    storeCelTime = registerSignal("storeCelTime");

    switchMode = new cMessage("switch");

    wifiOn = true;
    scheduleAt(simTime() + par("switchToCel").doubleValue(), switchMode);

    emit(queueLengthSignal, 0);

    capacity = par("capacity");
    queue.setName("queue");

    fifo = par("fifo");

    selectionStrategy = SelectionStrategy::create(par("sendingAlgorithm"), this, false);
    if (!selectionStrategy)
        throw cRuntimeError("invalid selection strategy");
}

void MyPassiveQueue::handleMessage(cMessage *msg)
{
    if (msg == switchMode){
       simtime_t newScheduleMode = wifiOn ? par("switchToWi").doubleValue() : par("switchToCel").doubleValue();
       if (wifiOn) {
           emit(storeCelTime, newScheduleMode);
           cQueue::Iterator scroll = cQueue::Iterator(queue);
           Job* tempJob = (Job*)scroll.operator ++().operator *();
           while (tempJob){
               EV << "sto eliminando le deadline" << endl;
               if ((cMessage*)tempJob->getContextPointer() != nullptr){
                   simtime_t oldScheduledTime = ((cMessage*)tempJob->getContextPointer())->getArrivalTime();
                   simtime_t created = ((cMessage*)tempJob->getContextPointer())->getSendingTime();
                   cancelAndDelete((cMessage*)tempJob->getContextPointer());
                   tempJob->setContextPointer(nullptr);
                   cMessage* deadline = new cMessage("deadline");
                   tempJob->setContextPointer(deadline);
                   deadline->setContextPointer(tempJob);
                   simtime_t totalDeadline = oldScheduledTime - created;
                   simtime_t residualDeadline = totalDeadline - (simTime() - created);
                   simtime_t reschedule = simTime() + residualDeadline + newScheduleMode;
                   scheduleAt(reschedule, deadline);
               }
           tempJob = (Job*)scroll.operator ++().operator *();
           }
       } else
           emit(storeWifiTime, newScheduleMode);
       scheduleAt(simTime() + newScheduleMode, switchMode);
       EV << "SWITCHED! wifiOn: " << wifiOn << " - next switch time: " << simTime() + newScheduleMode << endl;
       wifiOn = !wifiOn;
       cGate *out = gate("out", wifiOn ? 0:1);
       if(check_and_cast<IServer *>(out->getPathEndGate()->getOwnerModule())->isIdle() and !queue.isEmpty())
           request(wifiOn ? 0:1);
    }
    else if (!strcmp(msg->getName(), "deadline")){
        bool contained;
        contained = (Job*)queue.contains((Job*)msg->getContextPointer());
        if(contained){
            if(!wifiOn){
                Job *j;
                j = (Job*)queue.remove((Job*)msg->getContextPointer());
                emit(queueLengthSignal, length());
                //j->setTotalQueueingTime(0);
                j->setTotalQueueingTime(j->getTotalQueueingTime() + simTime() - j->getTimestamp());
                sendJob(j, 2);
            }
            ((Job*)msg->getContextPointer())->setContextPointer(nullptr);
        }
        delete msg;
   }else{
        Job *job = check_and_cast<Job *>(msg);
        job->setTimestamp();
        // check for container capacity
        if (capacity >= 0 && queue.getLength() >= capacity) {
           EV << "Queue full! Job dropped.\n";
           if (hasGUI())
               bubble("Dropped!");
           emit(droppedSignal, 1);
           delete msg;
           return;
        }
        cGate *out = gate("out", wifiOn ? 0:1);
        if (length() == 0 and check_and_cast<IServer *>(out->getPathEndGate()->getOwnerModule())->isIdle()) {
            // send through without queueing
            sendJob(job, wifiOn ? 0:1);
        }else{
            queue.insert(job);
            emit(queueLengthSignal, length());
            job->setQueueCount(job->getQueueCount() + 1);
            if(!wifiOn){
                cMessage* deadline = new cMessage("deadline");
                job->setContextPointer(deadline);
                deadline->setContextPointer(job);
                simtime_t deadlimit = par("deadline").doubleValue();
                scheduleAt(simTime() + deadlimit, deadline);
                emit(storeDeadline, deadlimit);
                EV << "job: " << job << " deadline: " << deadline << endl;
            }
            if(check_and_cast<IServer *>(out->getPathEndGate()->getOwnerModule())->isIdle())
                request(wifiOn ? 0:1);
        }
    }
}

void MyPassiveQueue::refreshDisplay() const
{
    // change the icon color
    getDisplayString().setTagArg("i", 1, queue.isEmpty() ? "" : "cyan");
}

int MyPassiveQueue::length()
{
    return queue.getLength();
}

void MyPassiveQueue::request(int gateIndex)
{
    if ((wifiOn and gateIndex==0) or (!wifiOn and gateIndex == 1)){
    Enter_Method("request()!");

    ASSERT(!queue.isEmpty());

    Job *job;
    if (fifo) {
        job = (Job *)queue.pop();
    }
    else {
        job = (Job *)queue.back();
        // FIXME this may have bad performance as remove uses linear search
        queue.remove(job);
    }
    emit(queueLengthSignal, length());

    job->setQueueCount(job->getQueueCount()+1);
    simtime_t d = simTime() - job->getTimestamp();
    job->setTotalQueueingTime(job->getTotalQueueingTime() + d);
    emit(queueingTimeSignal, d);
    if (job->getContextPointer()){
        cMessage *msg = (cMessage*)job->getContextPointer();
        cancelAndDelete(msg);
    }

        sendJob(job, gateIndex);
    }/*else{
        cGate *out = gate("out", wifiOn ? 0:1);
        if (check_and_cast<IServer *>(out->getPathEndGate()->getOwnerModule())->isIdle()){
            sendJob(job,  wifiOn ? 0:1);
        }
    }*/
}

void MyPassiveQueue::sendJob(Job *job, int gateIndex)
{
    cGate *out = gate("out", gateIndex);
    send(job, "out", gateIndex);
    if(gateIndex!=2)
        check_and_cast<IServer *>(out->getPathEndGate()->getOwnerModule())->allocate();
}

