# Copyright Software Improvement Group
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import subprocess


FONT = "fontname=\"sans-serif\""
NODE_STYLE = f"shape=\"box\" style=\"filled\" fillcolor=\"#1B64FF\" color=\"#FFFFFF\" fontcolor=\"#FFFFFF\" {FONT}"
EDGE_STYLE = f"fontcolor=\"#808087\" penwidth=\"2\" {FONT}"
DEFAULT_DEPENDENCY_COLOR = "color=\"#808087\""

ENTANGLEMENT_COLORS = {
    "CYCLIC_DEPENDENCY" : "color=\"#DB4A3D\"",
    "INDIRECT_CYCLIC_DEPENDENCY" : "color=\"#EF981A\"",
    "LAYER_BYPASSING_DEPENDENCY" : "color=\"#F8C640\""
}


def exportDot(architectureGraph, dotFile, format):
    with open(dotFile, "w", encoding="utf8") as f:
        f.write("digraph \"Graph\" {\n")
        f.write("compound=true\n")
        f.write("rankdir=TD\n")
        f.write(f"node [{NODE_STYLE}]\n")
        f.write(f"edge [{EDGE_STYLE}]\n")
        for component in architectureGraph.getTopLevelComponents():
            name = component.get("shortName") or component["name"]
            f.write(f"\"{component['id']}\" [label=\"{name}\"]\n")
        for source in architectureGraph.getTopLevelComponents():
            for target in architectureGraph.getTopLevelComponents():
                dependencyCount = architectureGraph.countDependencies(source, target)
                if dependencyCount > 0:
                    color = getDependencyColor(architectureGraph, source, target)
                    f.write(f"\"{source['id']}\" -> \"{target['id']}\" [label=\" {dependencyCount}\" {color}]\n")
        f.write("}\n")

    if format != "dot":
        subprocess.run(["dot", "-Tpdf", "-o", f"{dotFile}.{format}", dotFile])


def getDependencyColor(architectureGraph, source, target):
    for violation in architectureGraph.entanglement:
        ids = [source["name"], target["name"]]
        violationIds = [violation.get("sourceComponent"), violation.get("targetComponent")]

        if violation["type"] == "CYCLIC_DEPENDENCY" and set(ids) == set(violationIds):
            return ENTANGLEMENT_COLORS.get(violation["type"], DEFAULT_DEPENDENCY_COLOR)
        elif ids == violationIds:
            return ENTANGLEMENT_COLORS.get(violation["type"], DEFAULT_DEPENDENCY_COLOR)

    return DEFAULT_DEPENDENCY_COLOR
