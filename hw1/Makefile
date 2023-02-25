BUILD_DIR := ./build
SRC_DIR := ./src

_OBJS := main.o
OBJS := $(patsubst %.o,$(BUILD_DIR)/%.o,$(_OBJS))

CXX := g++
CPPFLAGS := -Ofast -g -Wall -std=c++20
LDFLAGS := -lpcap

.PHONY: all clean run

all:
	@mkdir -p $(BUILD_DIR)
	make $(BUILD_DIR)/main
	cp $(BUILD_DIR)/main main

$(BUILD_DIR)/main: $(OBJS) $(OBJS)
	$(CXX) $^ $(LDFLAGS) -o $@

$(BUILD_DIR)/%.o: $(SRC_DIR)/%.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CPPFLAGS) -c $< -o $@

run: $(BUILD_DIR)/main
	./main

clean:
	rm -r $(BUILD_DIR)
	rm -rf $(TEST_DEST_DIR)
	rm -f main

