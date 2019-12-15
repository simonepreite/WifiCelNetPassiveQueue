//
// This file is part of an OMNeT++/OMNEST simulation example.
//
// Copyright (C) 2006-2015 OpenSim Ltd.
//
// This file is distributed WITHOUT ANY WARRANTY. See the file
// `license' for details on this and other legal matters.
//



#include "IServer.h"
#include "Job.h"
#include "SelectionStrategies.h"

using namespace queueing;

//class SelectionStrategy;

/**
 * The queue MyServer. It cooperates with several Queues that which queue up
 * the jobs, and send them to MyServer on request.
 *
 * @see PassiveQueue
 */
class QUEUEING_API MyServer : public cSimpleModule, public IServer
{
    private:
        simsignal_t busySignal;
        simsignal_t serviceTime;
        bool allocated;
        simsignal_t responseTime;
        SelectionStrategy *selectionStrategy;

        Job *jobServiced;
        cMessage *endServiceMsg;

    public:
        MyServer();
        virtual ~MyServer();

    protected:
        virtual void initialize() override;
        virtual int numInitStages() const override {return 2;}
        virtual void handleMessage(cMessage *msg) override;
        virtual void refreshDisplay() const override;
        virtual void finish() override;

    public:
        virtual bool isIdle() override;
        virtual void allocate() override;
};


