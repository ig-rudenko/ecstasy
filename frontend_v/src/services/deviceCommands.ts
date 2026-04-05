import api from "@/services/api";

export interface StringValues {
    [key: string]: string;
}

export interface NullNumberValues {
    [key: string]: null | number;
}

export interface CommandContext {
    port?: StringValues;
    ip?: StringValues;
    mac?: StringValues;
    number?: NullNumberValues;
    word?: StringValues;
}

export interface DeviceCommandTemplate {
    id: number;
    name: string;
    description: string;
    command: string;
    device_vendor: string;
    context: CommandContext;
}

export interface CommandValidateResult {
    command: string;
    conditions: { expect: string; command: string }[];
}

export interface BulkCommandDeviceRef {
    deviceId: number;
    deviceName: string;
    detail?: string;
}

export interface BulkCommandTaskLaunch {
    taskId: string;
    devices: BulkCommandDeviceRef[];
    skipped: BulkCommandDeviceRef[];
}

export interface BulkCommandTaskStatus {
    taskId: string;
    status: string;
    progress?: number;
    processed?: number;
    total?: number;
    resultsCount: number;
    resultDeviceIds: number[];
    results: BulkCommandDeviceResult[];
}

export interface BulkCommandDeviceResult {
    deviceId: number;
    deviceName: string;
    status: string;
    commandId: number;
    commandText: string;
    output: string;
    detail: string;
    error: string;
    duration: number;
}

export const numberRegex = /\{number:?(-?\d+)?:?(-?\d+)?(#(\S+?)?)?}/;
export const portRegex = /\{port(#(\S+?)?)?}/;
export const ipRegex = /\{ip(#(\S+?)?)?}/;
export const macRegex = /\{mac(#(\S+?)?)?}/;
export const wordRegex = /\{word(#(\S+?)?)?}/;

/**
 * Returns a macro key name from a command placeholder.
 */
export function getCommandKeyName(key: string): string {
    const regex = /#(\S+)?}/;
    const match = regex.exec(key);
    if (match) {
        return match[1];
    }
    return "_";
}

/**
 * Creates an empty context for a command template.
 */
export function createCommandContext(command: string): CommandContext {
    const context: CommandContext = {
        number: {},
        port: {},
        ip: {},
        mac: {},
        word: {},
    };

    const numberRegexGlobal = /\{number:?(-?\d+)?:?(-?\d+)?(#(\S+?)?)?}/g;
    const portRegexGlobal = /\{port(#(\S+?)?)?}/g;
    const ipRegexGlobal = /\{ip(#(\S+?)?)?}/g;
    const macRegexGlobal = /\{mac(#(\S+?)?)?}/g;
    const wordRegexGlobal = /\{word(#(\S+?)?)?}/g;

    let match: RegExpExecArray | null;

    while ((match = numberRegexGlobal.exec(command)) !== null) {
        context.number![getCommandKeyName(match[0])] = null;
    }
    while ((match = portRegexGlobal.exec(command)) !== null) {
        context.port![getCommandKeyName(match[0])] = "";
    }
    while ((match = ipRegexGlobal.exec(command)) !== null) {
        context.ip![getCommandKeyName(match[0])] = "";
    }
    while ((match = macRegexGlobal.exec(command)) !== null) {
        context.mac![getCommandKeyName(match[0])] = "";
    }
    while ((match = wordRegexGlobal.exec(command)) !== null) {
        context.word![getCommandKeyName(match[0])] = "";
    }

    return context;
}

/**
 * Removes conditional prompt macros from a command preview.
 */
export function stripConditionalMacros(command: string): string {
    return command.replaceAll(/\{if.+(?<!\\)}/g, "");
}

/**
 * Deep clones a command template.
 */
export function cloneCommandTemplate(command: DeviceCommandTemplate): DeviceCommandTemplate {
    return {
        ...command,
        context: {
            port: {...(command.context.port || {})},
            ip: {...(command.context.ip || {})},
            mac: {...(command.context.mac || {})},
            number: {...(command.context.number || {})},
            word: {...(command.context.word || {})},
        },
    };
}

/**
 * Prepares command templates returned by API for the UI.
 */
export function hydrateDeviceCommands(commands: DeviceCommandTemplate[]): DeviceCommandTemplate[] {
    return commands.map((command) => ({
        ...command,
        command: stripConditionalMacros(command.command),
        context: createCommandContext(command.command),
    }));
}

/**
 * Returns human-readable description for a numeric macro range.
 */
export function numberVerboseRange(commandPart: string): string {
    const numberMatch = numberRegex.exec(commandPart);
    if (numberMatch && numberMatch.length >= 3 && numberMatch[1] && numberMatch[2]) {
        return `целое число от ${Number(numberMatch[1])} до ${Number(numberMatch[2])}`;
    }
    return "любое целое число";
}

/**
 * Returns min value for a numeric macro if present.
 */
export function numberMinValue(commandPart: string): number | undefined {
    const numberMatch = numberRegex.exec(commandPart);
    if (numberMatch && numberMatch[1]) {
        return Number(numberMatch[1]);
    }
}

/**
 * Returns max value for a numeric macro if present.
 */
export function numberMaxValue(commandPart: string): number | undefined {
    const numberMatch = numberRegex.exec(commandPart);
    if (numberMatch && numberMatch[2]) {
        return Number(numberMatch[2]);
    }
}

/**
 * Normalizes MAC address input.
 */
export function cleanMacAddress(mac: string): string {
    const cleaned = mac.toUpperCase().match(/[0-9A-F]/g);
    return cleaned && cleaned.length === 12 ? cleaned.join("") : "";
}

/**
 * Validates word macro value.
 */
export function isValidWord(word: string): boolean {
    return /^\S+$/.test(word);
}

/**
 * Validates IPv4 input.
 */
export function isValidIPAddress(ip: string): boolean {
    const ipRegexValue = /^(25[0-5]|2[0-4][0-9]|1?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|1?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|1?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|1?[0-9][0-9]?)$/;
    return ipRegexValue.test(ip);
}

/**
 * Checks whether all command fields are filled correctly.
 */
export function commandIsValid(command: DeviceCommandTemplate): boolean {
    if (command.context.port) {
        for (const key in command.context.port) {
            if (!command.context.port[key].length) return false;
        }
    }
    if (command.context.ip) {
        for (const key in command.context.ip) {
            if (!isValidIPAddress(command.context.ip[key])) return false;
        }
    }
    if (command.context.mac) {
        for (const key in command.context.mac) {
            if (!cleanMacAddress(command.context.mac[key])) return false;
        }
    }
    if (command.context.word) {
        for (const key in command.context.word) {
            if (!isValidWord(command.context.word[key])) return false;
        }
    }
    if (command.context.number) {
        for (const key in command.context.number) {
            if (command.context.number[key] == null || isNaN(command.context.number[key] as number)) return false;
        }
    }
    return true;
}

/**
 * Loads commands for a single device.
 */
export async function fetchDeviceCommands(deviceName: string): Promise<DeviceCommandTemplate[]> {
    const response = await api.get<DeviceCommandTemplate[]>(`/api/v1/devices/${deviceName}/commands`);
    return hydrateDeviceCommands(response.data);
}

/**
 * Validates rendered commands for a single device.
 */
export async function validateDeviceCommand(deviceName: string, command: DeviceCommandTemplate): Promise<string> {
    const response = await api.post<{ command: CommandValidateResult[] }>(
        `/api/v1/devices/${deviceName}/commands/${command.id}/validate`,
        command.context,
    );

    return response.data.command.map((item) => item.command).join("\n");
}

/**
 * Executes a command on a single device.
 */
export async function executeDeviceCommand(deviceName: string, command: DeviceCommandTemplate): Promise<string> {
    const response = await api.post<{ output: string }>(
        `/api/v1/devices/${deviceName}/commands/${command.id}/execute`,
        command.context,
    );
    return response.data.output;
}

/**
 * Starts bulk command execution task.
 */
export async function executeBulkDeviceCommand(
    commandId: number,
    deviceIds: number[],
    context: CommandContext,
): Promise<BulkCommandTaskLaunch> {
    const response = await api.post<BulkCommandTaskLaunch>(
        `/api/v1/devices/commands/${commandId}/execute-multiple`,
        {
            ...context,
            device_ids: deviceIds,
        },
    );
    return response.data;
}

/**
 * Loads bulk task status.
 */
export async function getBulkCommandTaskStatus(taskId: string): Promise<BulkCommandTaskStatus> {
    const response = await api.get<BulkCommandTaskStatus>(`/api/v1/devices/commands/tasks/${taskId}`);
    return response.data;
}
