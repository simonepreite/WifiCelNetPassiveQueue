//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Lesser General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
// 
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Lesser General Public License for more details.
// 
// You should have received a copy of the GNU Lesser General Public License
// along with this program.  If not, see http://www.gnu.org/licenses/.
//

import org.omnetpp.queueing.Classifier;
import org.omnetpp.queueing.PassiveQueue;
import org.omnetpp.queueing.Queue;
import org.omnetpp.queueing.Server;
import org.omnetpp.queueing.Sink;
import org.omnetpp.queueing.Source;

network WifiCelNetPassiveQueue
{
    @display("bgb=634,436");
    submodules:
        sink: Sink {
            @display("p=513,99");
        }
        OFFLOAD: MyPassiveQueue {
            @display("p=202,225");
        }
        LOCAL: Queue {
            @display("p=204,103");
        }
        REMOTE: Queue {
            @display("p=509,236");
        }
        WIFI: MyServer {
            @display("p=363,182");
        }
        CELL: MyServer {
            @display("p=364,304");
        }
        source: Source {
            @display("p=51,224");
        }
    connections:
        source.out --> OFFLOAD.in++;
        OFFLOAD.out[0] --> WIFI.in++;
        OFFLOAD.out[1] --> CELL.in++;
        WIFI.out --> REMOTE.in++;
        CELL.out --> REMOTE.in++;
        REMOTE.out --> sink.in++;
        OFFLOAD.out[2] --> LOCAL.in++;
        LOCAL.out --> sink.in++;
}
