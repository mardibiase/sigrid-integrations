#  Copyright Software Improvement Group
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from report_generator.generator.constants import MetricEnum


class TestPlaceholders:

    def test_to_json_name(self):
        class TestMetricEnum(MetricEnum):
            UNIT_SIZE = "UNIT_SIZE"
            DUPLICATION = "DUPLICATION"
            duplication = "duplication"
            UnIt_sIze = "UnIt_sIze"


        assert TestMetricEnum.UNIT_SIZE.to_json_name() == "unitSize"
        assert TestMetricEnum.DUPLICATION.to_json_name() == "duplication"
        assert TestMetricEnum.duplication.to_json_name() == "duplication"
        assert TestMetricEnum.UnIt_sIze.to_json_name() == "unitSize"
