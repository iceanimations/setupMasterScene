import pymel.core as pc
if not pc.pluginInfo('redshift4maya', q=True, loaded=True):
    pc.loadPlugin('redshift4maya')
mel = '''
global proc string redshiftCreateMeshParametersNode2()
{
    string $allSelected[] = `ls -selection -l`;
    string $selectedDagObjects[] = `ls -selection -l`;

    int $ni = size($selectedDagObjects);
    for($i=0; $i<$ni; $i++)
    {
        string $alreadyConnected[] = `listConnections -type "RedshiftMeshParameters" $selectedDagObjects[$i]`;
        for($j=0; $j<size($alreadyConnected); $j++)
        {
            sets -e -remove $alreadyConnected[$j];
            if(size(`listConnections $alreadyConnected[$j]`) == 0)
                delete $alreadyConnected[$j];
        }
    }
    $rsMeshParameters = `createNode RedshiftMeshParameters`;
    sets -e -forceElement $rsMeshParameters $selectedDagObjects;
    
    select -r -ne $rsMeshParameters;
    return $rsMeshParameters;
}

global proc string redshiftCreateMatteParametersNode2()
{
    string $allSelected[] = `ls -selection -l`;
    string $selectedDagObjects[] = `ls -selection -l`;

    int $ni = size($selectedDagObjects);
    for($i=0; $i<$ni; $i++)
    {
        string $alreadyConnected[] = `listConnections -type "RedshiftMatteParameters" $selectedDagObjects[$i]`;
        for($j=0; $j<size($alreadyConnected); $j++)
        {
            sets -e -remove $alreadyConnected[$j];
            if(size(`listConnections $alreadyConnected[$j]`) == 0)
                delete $alreadyConnected[$j];
        }
    }
    $rsMatteParameters = `createNode RedshiftMatteParameters`;
    sets -e -forceElement $rsMatteParameters $selectedDagObjects;

    select -r -ne $rsMatteParameters;
    return $rsMatteParameters;
}

global proc string redshiftCreateVisibilityNode2()
{
    string $allSelected[] = `ls -selection -l`;
    string $selectedDagObjects[] = `ls -selection -l`;

    int $ni = size($selectedDagObjects);
    for($i=0; $i<$ni; $i++)
    {
        string $alreadyConnected[] = `listConnections -type "RedshiftVisibility" $selectedDagObjects[$i]`;
        for($j=0; $j<size($alreadyConnected); $j++)
        {
            sets -e -remove $alreadyConnected[$j];
            if(size(`listConnections $alreadyConnected[$j]`) == 0)
                delete $alreadyConnected[$j];
        }
    }
    $rsVisibilityParameters = `createNode RedshiftVisibility`;
    sets -e -forceElement $rsVisibilityParameters $selectedDagObjects;

    select -r -ne $rsVisibilityParameters;
    return $rsVisibilityParameters;
}
'''
pc.mel.eval(mel)

import src.mainUi as mu
reload(mu)
Window = mu.MainUi