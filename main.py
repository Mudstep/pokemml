import re, argparse


class Main:
    def __init__(self, f_name, f_mml, f_asm):
        self.out_name = f_name
        self.mml_in = open(f_mml)
        self.asm_out = open(f_asm, 'w')
        self.mml_lines = self.mml_in.read().split('\n')
        self.mml_lines_index = 0
        self.channel_count = 0
        self.channel_flags = [False, False, False, False]

        for i in range(len(self.mml_lines)):
            l = self.mml_lines[i].split('#')[0]
            self.mml_lines[i] = l

    def main(self):
        self.asm_out.write(f'Music_{self.out_name}:')

        self.asm_out.write('\n')

        for lin in self.mml_lines:
            if lin == '{1}':
                self.channel_count += 1
                self.channel_flags[0] = True
            elif lin == '{2}':
                self.channel_count += 1
                self.channel_flags[1] = True
            elif lin == '{3}':
                self.channel_count += 1
                self.channel_flags[2] = True
            elif lin == '{4}':
                self.channel_count += 1
                self.channel_flags[3] = True

        self.asm_out.write(f'\tchannel_count {self.channel_count}\n')

        if self.channel_flags[0]:
            self.asm_out.write(f'\tchannel 1, Music_{self.out_name}_Ch1\n')
        if self.channel_flags[1]:
            self.asm_out.write(f'\tchannel 2, Music_{self.out_name}_Ch2\n')
        if self.channel_flags[2]:
            self.asm_out.write(f'\tchannel 3, Music_{self.out_name}_Ch3\n')
        if self.channel_flags[3]:
            self.asm_out.write(f'\tchannel 4, Music_{self.out_name}_Ch4\n')

        while self.mml_lines_index < len(self.mml_lines):
            line = self.mml_lines[self.mml_lines_index]
            self.mml_lines_index += 1
            if '{1}' in line:
                self.write_channel(1)
            if '{2}' in line:
                self.write_channel(2)
            if '{3}' in line:
                self.write_channel(3)
            if '{4}' in line:
                self.write_channel(4)
            if '#' in line:
                continue

        self.asm_out.close()

    def write_channel(self, channel_index):
        current_octave = 0
        current_volume = None
        current_decay = 0
        default_notelength = 16
        default_drum_speed = 12
        default_volume = 12
        command_string = ''
        loop_stack = []
        num_loops_found = 0
        has_main_loop = False
        found_sub = False

        self.asm_out.write(f'Music_{self.out_name}_Ch{channel_index}:\n')

        while self.mml_lines_index < len(self.mml_lines):
            line = self.mml_lines[self.mml_lines_index]
            self.mml_lines_index += 1
            if line == ';' + str(channel_index):
                break
            command_string += line

        tkn = Tokenizer()
        tkn_list = tkn.run(command_string)

        command_groups = []
        for i, token in enumerate(tkn_list):
            if token[0] == 'ERROR':
                print('ERROR')
                return
            if token[0] == 'NUMBER': continue
            if token[0] == 'COMMA': continue
            arg_tkn = []
            for j in range(i + 1, len(tkn_list)):
                if tkn_list[j][0] == 'NUMBER':
                    arg_tkn.append(tkn_list[j])
                elif tkn_list[j][0] == 'COMMA':
                    continue
                else:
                    break
            command_groups.append( (token, arg_tkn) )

        for cmd, args in command_groups:
            if cmd[1] == 'l':
                assert len(args) == 1
                default_notelength = args[0][1]
            elif cmd[1] in ('c+', 'c', 'd+', 'd', 'e', 'f+', 'f', 'g+', 'g', 'a+', 'a', 'b+', 'b'):
                assert len(args) in (0, 1)
                note_length = default_notelength
                note_type = cmd[1].upper()
                if len(note_type) == 1:
                    note_type = note_type + '_'
                else:
                    note_type = note_type[0] + '#'

                if len(args) == 1:
                    note_length = args[0][1]

                note_ties = note_length.split('^')
                note_length = sum([nl_dict[x] for x in note_ties])

                self.asm_out.write(f'\tnote {note_type}, {note_length}\n')
            elif cmd[1] == 'x':
                # assert len(args) in (1, 2)
                note_length = default_notelength
                note_type = args[0][1]

                if len(args) == 2:
                    note_length = args[1][1]

                note_ties = note_length.split('^')
                note_length = sum([nl_dict[x] for x in note_ties])

                self.asm_out.write(f'\tdrum_note {note_type}, {note_length}\n')
            elif cmd[1] == 'r':
                assert len(args) in (0, 1)
                rest_length = default_notelength

                if len(args) == 1:
                    rest_length = args[0][1]

                rest_ties = rest_length.split('^')
                rest_length = sum([nl_dict[x] for x in rest_ties])

                self.asm_out.write(f'\trest {rest_length}\n')
            elif cmd[1] == 'o':
                assert len(args) == 1
                current_octave = int(args[0][1])
                self.asm_out.write(f'\toctave {current_octave}\n')
            elif cmd[1] == '<':
                assert len(args) == 0
                current_octave += 1
                self.asm_out.write(f'\toctave {current_octave}\n')
            elif cmd[1] == '>':
                assert len(args) == 0
                current_octave -= 1
                self.asm_out.write(f'\toctave {current_octave}\n')
            elif cmd[1] == '[':
                assert len(args) in (0, 1)
                if len(args) == 1:
                    loop_ct = int(args[0][1])
                else:
                    loop_ct = 2
                self.asm_out.write(f'.loop{num_loops_found}:\n')
                loop_stack.append((num_loops_found, loop_ct))
                num_loops_found += 1
            elif cmd[1] == ']':
                assert len(args) == 0
                assert len(loop_stack) > 0
                cur_loop = loop_stack.pop()
                self.asm_out.write(f'\tsound_loop {cur_loop[1]}, .loop{cur_loop[0]}\n')
            elif cmd[1] == '$':
                assert len(args) == 1
                assert int(args[0][1]) == channel_index
                self.asm_out.write('.mainloop:\n')
                has_main_loop = True
            elif cmd[1] == 'v':
                assert len(args) in (1, 2)
                if len(args) == 2:
                    current_decay = int(args[1][1])
                current_volume = int(args[0][1])
                self.asm_out.write(f'\tvolume_envelope {current_volume}, {current_decay}\n')
            elif cmd[1] == 't':
                assert len(args) == 1
                self.asm_out.write(f'\ttempo {args[0][1]}\n')
            elif cmd[1] == 'k':
                assert len(args) == 1
                self.asm_out.write(f'\tpitch_offset {args[0][1]}\n')
            elif cmd[1] == 'p':
                assert len(args) == 1
                assert int(args[0][1]) in (0, 1, 2)
                if int(args[0][1]) == 0:
                    cmd_arg = 'TRUE, FALSE'
                elif int(args[0][1]) == 1:
                    cmd_arg = 'TRUE, TRUE'
                else:
                    cmd_arg = 'FALSE, TRUE'
                self.asm_out.write(f'\tstereo_panning {cmd_arg}\n')
            elif cmd[1] == '|':
                assert len(args) == 1
                if channel_index in (1, 2):
                    assert int(args[0][1]) in (0, 1, 2, 3)
                    self.asm_out.write(f'\tduty_cycle {args[0][1]}\n')
                elif channel_index == 3:
                    if current_volume is None:
                        current_volume = 7
                    self.asm_out.write(f'\tvolume_envelope {current_volume}, {args[0][1]}\n')
                elif channel_index == 4:
                    self.asm_out.write(f'\ttoggle_noise {args[0][1]}\n')
            elif cmd[1] == 'm':
                assert len(args) == 3
                self.asm_out.write(f'\tvibrato {args[0][1]}, {args[1][1]}, {args[2][1]}\n')
            elif cmd[1] == 'n':
                assert len(args) == 3
                self.asm_out.write(f'\tnote_type {args[0][1]}, {args[1][1]}, {args[2][1]}\n')
            elif cmd[1] == '%p':
                assert len(args) == 2
                self.asm_out.write(f'\tvolume {args[0][1]}, {args[1][1]}\n')
            elif cmd[1] == '%s':
                assert len(args) == 1
                self.asm_out.write(f'\tdrum_speed {args[0][1]}\n')
            elif cmd[1] == '&':
                assert len(args) == 1
                self.asm_out.write(f'\tsound_call .sub{args[0][1]}\n')
            elif cmd[1] == '(':
                assert len(args) == 1
                if not found_sub:
                    if has_main_loop:
                        self.asm_out.write('\tsound_loop 0, .mainloop\n')
                    else:
                        self.asm_out.write('\tsound_ret\n')
                    found_sub = True
                self.asm_out.write(f'.sub{args[0][1]}:\n')
            elif cmd[1] == ')':
                assert len(args) == 0
                self.asm_out.write('\tsound_ret\n')
            elif cmd[1] == '%m':
                assert len(args) == 3
                self.asm_out.write(f'\tpitch_slide {args[0][1]}, {args[1][1]}, {args[2][1]}\n')
            elif cmd[1] == '%t':
                assert len(args) == 2
                self.asm_out.write(f'\ttranspose {args[0][1]}, {args[1][1]}\n')
            elif cmd[1] == '?s':
                assert len(args) == 4
                self.asm_out.write(f'\tsquare_note {args[0][1]}, {args[1][1]}, {args[2][1]}, {args[3][1]}\n')
            elif cmd[1] == '?n':
                assert len(args) == 4
                self.asm_out.write(f'\tnoise_note {args[0][1]}, {args[1][1]}, {args[2][1]}, {args[3][1]}\n')
            elif cmd[1] == '?p':
                assert len(args) == 2
                self.asm_out.write(f'\tpitch_sweep {args[0][1]}, {args[1][1]}\n')
            elif cmd[1] == '?d':
                assert len(args) == 4
                self.asm_out.write(f'\tduty_cycle_pattern {args[0][1]}, {args[1][1]}, {args[2][1]}, {args[3][1]}\n')
            elif cmd[1] == '?e':
                assert len(args) == 0
                self.asm_out.write('f\tforce_stereo_panning{args[0][1]}, {args[1][1]}\n')
            elif cmd[1] == '?f':
                assert len(args) == 0
                self.asm_out.write('\tf\n')

        if not found_sub:
            if has_main_loop:
                self.asm_out.write('\tsound_loop 0, .mainloop\n')
            else:
                self.asm_out.write('\tsound_ret\n')

        self.asm_out.write('\n')

        print(command_groups)

        print(tkn_list)


command_list = ('l', 'c+', 'c', 'd+', 'd', 'e', 'f+', 'f', 'g+', 'g', 'a+', 'a', 'b+', 'b', 'r',
 '<', '>', 'o', '[', ']', 'j', 'v', 'p', 't', 'k', 'm', '$', '|', '%p', '%s', '%m', 'n', 'x', '&', '(', ')',
 '?s', '?n', '?t', '?p', '?e', '?f')
command_re = ('(' + '|'.join([re.escape(cmd) for cmd in command_list]) + ')')
print(command_re)
command_re = re.compile('(' + '|'.join([re.escape(cmd) for cmd in command_list]) + ')')

nl_dict = { '1': 16,
            '2.': 12,
            '2': 8,
            '4.': 6,
            '4': 4,
            '8.': 3,
            '8': 2,
            '16': 1,
            '32': 1,
            '64': 1,
            # Triplets (DO NOT USE)
            '48': 1,
            '24': 1,
            '12': 1,
            '6': 3,
            '3': 5,
}


class Tokenizer:
    def __init__(self):
        self.tokens = []

    def run(self, s):
        cur_loc = 0
        while cur_loc < len(s):
            if s[cur_loc] == ' ':
                cur_loc += 1
                continue
            new_token = self.get_next_token(s[cur_loc:])
            cur_loc += len(new_token[1])
            self.tokens.append(new_token)
        return self.tokens

    def get_next_token(self, s):
        cmd_check = command_re.match(s)
        if cmd_check is not None:
            cmd_text = cmd_check.groups()[0]
            return ('COMMAND', cmd_text)
        num_check = re.match(r'([\-0-9.^]+)', s)
        if num_check is not None:
            num_text = num_check.groups()[0]
            return ('NUMBER', num_text)
        if s[0] == ',':
            return ('COMMA', ',')
        return ('ERROR', s[0])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('songname')
    parser.add_argument('mmlfile')
    parser.add_argument('asmfile')

    args = parser.parse_args()

    main = Main(args.songname, args.mmlfile, args.asmfile)
    main.main()
